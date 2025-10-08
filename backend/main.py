from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

app = FastAPI(title="MARVIN API", description="AI-Powered Code Editor API", version="1.0.0")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class CreateFileRequest(BaseModel):
    filename: str
    content: str
    language: Optional[str] = "python"

class CodeRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    filename: Optional[str] = "untitled"

class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "MARVIN backend is running",
        "version": "1.0.0",
        "endpoints": ["/create", "/upload", "/analyze", "/optimize"]
    }

# /create endpoint - Create a new file
@app.post("/create")
async def create_file(request: CreateFileRequest):
    try:
        # Demo response - ready for expansion with actual file creation
        return {
            "status": "success",
            "message": f"File '{request.filename}' created successfully",
            "data": {
                "filename": request.filename,
                "language": request.language,
                "content_length": len(request.content),
                "lines_of_code": len(request.content.split('\n')),
                "accepted": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# /upload endpoint - Upload a file
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Determine language from file extension
        extension = file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'cpp': 'c++',
            'java': 'java',
            'html': 'html',
            'css': 'css',
            'json': 'json'
        }
        language = language_map.get(extension, extension)
        
        # Demo response - ready for expansion with actual file processing
        return {
            "status": "success",
            "message": f"File '{file.filename}' uploaded successfully",
            "data": {
                "filename": file.filename,
                "file_size": file_size,
                "language": language,
                "extension": extension,
                "content_type": file.content_type,
                "accepted": True,
                "ready_for_processing": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# /analyze endpoint - Analyze code
@app.post("/analyze")
async def analyze_code(request: CodeRequest):
    try:
        lines = request.code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Demo analysis - ready for expansion with actual AI analysis
        analysis = {
            "complexity": "medium",
            "quality_score": 85,
            "issues_found": 2,
            "suggestions": [
                "Consider adding docstrings for better documentation",
                "Some functions could be optimized for better performance"
            ],
            "metrics": {
                "total_lines": len(lines),
                "code_lines": len(non_empty_lines),
                "blank_lines": len(lines) - len(non_empty_lines),
                "estimated_time": "2 minutes"
            }
        }
        
        return {
            "status": "success",
            "message": f"Code analysis completed for {request.filename}",
            "data": {
                "filename": request.filename,
                "language": request.language,
                "analysis": analysis,
                "accepted": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# /optimize endpoint - Optimize code
@app.post("/optimize")
async def optimize_code(request: CodeRequest):
    try:
        # Demo optimization - ready for expansion with actual AI optimization
        optimized_code = request.code  # Placeholder for actual optimization
        
        optimization_report = {
            "improvements_made": 5,
            "performance_gain": "15%",
            "changes": [
                "Removed redundant variables",
                "Optimized loop structures",
                "Improved function signatures",
                "Added type hints",
                "Refactored for better readability"
            ],
            "before_size": len(request.code),
            "after_size": len(optimized_code),
            "reduction": "0%"  # Placeholder until real optimization
        }
        
        return {
            "status": "success",
            "message": f"Code optimization completed for {request.filename}",
            "data": {
                "filename": request.filename,
                "language": request.language,
                "optimized_code": optimized_code,
                "optimization_report": optimization_report,
                "accepted": True,
                "ready_for_ai_expansion": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MARVIN API",
        "all_endpoints_active": True
    }
