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
from pydantic import BaseModel, Field, validator

# --- App setup ---
app = FastAPI(
    title="MARVIN API", 
    description="AI-Powered Code Editor API", 
    version="1.1.0"
)

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
            "message": str(exc),
            "type": type(exc).__name__
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

# Custom error response for connection errors
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested API endpoint does not exist. Make sure the backend is running.",
            "path": str(request.url.path)
        }
    )

# --- Storage setup (safe for serverless) ---
# Prefer ephemeral /tmp in serverless like Vercel; fallback to local 'storage' for dev
BASE_STORAGE = Path(os.environ.get("MARVIN_STORAGE_DIR", "/tmp/marvin_storage"))
FILES_DIR = BASE_STORAGE / "files"
ANALYSIS_DIR = BASE_STORAGE / "analysis"
FILES_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions for security
ALLOWED_EXTS = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "tsx": "tsx",
    "jsx": "jsx",
    "cpp": "c++",
    "c": "c",
    "java": "java",
    "html": "html",
    "css": "css",
    "json": "json",
    "md": "markdown",
}

# --- Pydantic models ---
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="python")

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    language: str

class AnalysisRequest(BaseModel):
    file_id: str

class AnalysisResponse(BaseModel):
    file_id: str
    summary: Dict[str, Any]
    issues: List[Dict[str, Any]]
    suggestions: List[str]

class OptimizationRequest(BaseModel):
    file_id: str
    optimization_type: str = Field(default="performance")

class OptimizationResponse(BaseModel):
    file_id: str
    optimized_code: str
    changes: List[Dict[str, Any]]
    metrics: Dict[str, Any]

# --- Utility functions ---
def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]

def detect_language(filename: str) -> Optional[str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ALLOWED_EXTS.get(ext)

def analyze_python_code(code: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(code)
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        
        return {
            "functions": functions,
            "classes": classes,
            "imports": list(set(imports)),
            "lines": len(code.splitlines()),
        }
    except SyntaxError as e:
        return {"error": f"Syntax error: {str(e)}", "line": e.lineno}

def detect_code_issues(code: str, language: str) -> List[Dict[str, Any]]:
    issues = []
    lines = code.splitlines()
    
    if language == "python":
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "print(" in stripped and not stripped.startswith("#"):
                issues.append({
                    "line": i,
                    "type": "debug_code",
                    "message": "Consider removing debug print statements",
                    "severity": "low"
                })
            if "TODO" in stripped or "FIXME" in stripped:
                issues.append({
                    "line": i,
                    "type": "todo",
                    "message": "Unresolved TODO/FIXME comment",
                    "severity": "info"
                })
    
    return issues

def generate_suggestions(code: str, language: str) -> List[str]:
    suggestions = []
    if language == "python":
        if "import *" in code:
            suggestions.append("Avoid wildcard imports for better code clarity")
        if code.count("\n") > 300:
            suggestions.append("Consider splitting this file into smaller modules")
        if "global " in code:
            suggestions.append("Minimize use of global variables")
    return suggestions

# --- API Routes with /api prefix ---

@app.get("/api/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "service": "MARVIN API",
        "version": "1.1.0",
        "timestamp": time.time()
    })

@app.post("/api/create", response_model=dict)
async def create_project(project: ProjectCreate):
    project_id = hashlib.sha256(f"{project.name}{time.time()}".encode()).hexdigest()[:16]
    project_dir = FILES_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "project_id": project_id,
        "name": project.name,
        "language": project.language,
        "created_at": time.time()
    }
    
    with open(project_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    return JSONResponse({
        "project_id": project_id,
        "message": "Project created successfully",
        "metadata": metadata
    })

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    language = detect_language(file.filename)
    if not language:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed extensions: {', '.join(ALLOWED_EXTS.keys())}"
        )
    
    content = await file.read()
    file_id = compute_file_hash(content)
    file_path = FILES_DIR / f"{file_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return JSONResponse({
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "language": language
    })

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_code(req: AnalysisRequest):
    matching_files = list(FILES_DIR.glob(f"{req.file_id}_*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = matching_files[0]
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    language = detect_language(file_path.name)
    summary = analyze_python_code(code) if language == "python" else {"lines": len(code.splitlines())}
    issues = detect_code_issues(code, language or "")
    suggestions = generate_suggestions(code, language or "")
    
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
