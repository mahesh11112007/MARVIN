import os
import io
import ast
import time
import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator

# --- App setup ---
app = FastAPI(
    title="MARVIN API", 
    description="AI-Powered Code Editor API", 
    version="1.1.0"
)

# Templates setup
templates = Jinja2Templates(directory="../templates")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler to always return JSON instead of HTML
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

# --- Configuration and Directories ---
BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "uploaded_files"
FILES_DIR.mkdir(exist_ok=True)

ANALYSIS_DIR = BASE_DIR / "analysis_results"
ANALYSIS_DIR.mkdir(exist_ok=True)

# --- Pydantic Models ---
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    message: str

class CodeAnalysisRequest(BaseModel):
    file_id: str
    analysis_type: str = "basic"  # basic, security, performance

class AnalysisResponse(BaseModel):
    file_id: str
    summary: Dict[str, Any]
    issues: List[Dict[str, str]]
    suggestions: List[str]
    timestamp: float

class OptimizationRequest(BaseModel):
    file_id: str
    optimization_type: str = "performance"  # performance, readability, security

class OptimizationResponse(BaseModel):
    file_id: str
    optimized_code: str
    changes: List[Dict[str, str]]
    metrics: Dict[str, Any]

# --- Root endpoint ---
@app.get("/")
async def root(request: Request):
    """Render the landing page"""
    return templates.TemplateResponse("index.html", {"request": request})

# --- Health Check ---
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# --- File Upload Endpoint ---
@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_code_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are supported")
    
    # Generate unique file ID
    file_id = hashlib.md5(f"{file.filename}{time.time()}".encode()).hexdigest()[:12]
    
    # Save the file
    file_path = FILES_DIR / f"{file_id}_{file.filename}"
    content = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return JSONResponse({
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "message": "File uploaded successfully"
    })

# --- Code Analysis Endpoint ---
@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_code(req: CodeAnalysisRequest):
    # Find the file
    matching_files = list(FILES_DIR.glob(f"{req.file_id}_*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = matching_files[0]
    
    # Read and parse the file
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Syntax error: {str(e)}")
    
    # Perform analysis
    summary = {
        "total_lines": len(code.splitlines()),
        "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
        "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
        "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
    }
    
    issues = []
    suggestions = []
    
    # Check for common issues
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
            issues.append({"type": "missing_docstring", "message": f"Function {node.name} lacks a docstring"})
        
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({"type": "bare_except", "message": "Bare except clause detected"})
    
    suggestions.append("Consider adding type hints to function parameters")
    suggestions.append("Ensure all functions have descriptive docstrings")
    
    # Save analysis results
    analysis_file = ANALYSIS_DIR / f"{req.file_id}_analysis.json"
    analysis_data = {
        "file_id": req.file_id,
        "summary": summary,
        "issues": issues,
        "suggestions": suggestions,
        "timestamp": time.time()
    }
    
    with open(analysis_file, "w") as f:
        json.dump(analysis_data, f, indent=2)
    
    return JSONResponse(analysis_data)

# --- Code Optimization Endpoint ---
@app.post("/api/optimize", response_model=OptimizationResponse)
async def optimize_code(req: OptimizationRequest):
    matching_files = list(FILES_DIR.glob(f"{req.file_id}_*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = matching_files[0]
    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()
    
    optimized_code = original_code
    changes = []
    
    # Simple optimization example
    if req.optimization_type == "performance":
        if "print(" in original_code:
            optimized_code = "\n".join(
                line for line in original_code.splitlines()
                if "print(" not in line or line.strip().startswith("#")
            )
            changes.append({
                "type": "removed_debug_prints",
                "description": "Removed debug print statements"
            })
    
    metrics = {
        "original_lines": len(original_code.splitlines()),
        "optimized_lines": len(optimized_code.splitlines()),
        "reduction": len(original_code) - len(optimized_code)
    }
    
    return JSONResponse({
        "file_id": req.file_id,
        "optimized_code": optimized_code,
        "changes": changes,
        "metrics": metrics
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
