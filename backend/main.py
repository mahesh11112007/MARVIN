import os
import io
import ast
import time
import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# --- App setup ---
app = FastAPI(title="MARVIN API", description="AI-Powered Code Editor API", version="1.1.0")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
class CreateFileRequest(BaseModel):
    filename: str = Field(..., description="File name with extension")
    content: str
    language: Optional[str] = None

    @validator("filename")
    def validate_filename(cls, v: str) -> str:
        if "/" in v or ".." in v:
            raise ValueError("Invalid filename")
        if not any(v.endswith(f".{ext}") for ext in ALLOWED_EXTS):
            raise ValueError("Unsupported file extension")
        return v

class CodeRequest(BaseModel):
    code: str
    language: Optional[str] = None
    filename: Optional[str] = "untitled"

class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None

# --- Helpers ---

def detect_language_from_name(name: str) -> str:
    ext = name.split(".")[-1].lower() if "." in name else ""
    return ALLOWED_EXTS.get(ext, ext or "plain")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def safe_write_file(path: Path, content: bytes) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "modified": int(stat.st_mtime),
        "sha256": sha256_bytes(content),
    }


def analyze_python(code: str) -> Dict[str, Any]:
    """Static analysis for Python using ast and simple heuristics."""
    issues: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip()]
    metrics.update(
        total_lines=len(lines),
        code_lines=len(non_empty),
        blank_lines=len(lines) - len(non_empty),
        avg_line_length=(sum(len(l) for l in lines) / len(lines)) if lines else 0,
    )

    try:
        tree = ast.parse(code)
        func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        class_defs = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        metrics.update(functions=len(func_defs), classes=len(class_defs))
        # Docstring checks
        for f in func_defs:
            if ast.get_docstring(f) in (None, ""):
                issues.append({
                    "type": "style",
                    "message": f"Function '{f.name}' is missing a docstring",
                    "lineno": getattr(f, "lineno", None),
                    "severity": "low",
                })
        # Cyclomatic complexity (rough heuristic)
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.Try, ast.With, ast.BoolOp)):
                complexity += 1
        metrics["estimated_cyclomatic_complexity"] = complexity
    except SyntaxError as e:
        issues.append({
            "type": "syntax",
            "message": str(e),
            "lineno": getattr(e, "lineno", None),
            "severity": "high",
        })

    # Long line check
    long_lines = [i + 1 for i, l in enumerate(lines) if len(l) > 120]
    if long_lines:
        issues.append({
            "type": "style",
            "message": f"Found {len(long_lines)} lines longer than 120 characters",
            "lines": long_lines,
            "severity": "low",
        })

    quality_score = max(0, 100 - len(issues) * 3 - max(0, metrics.get("estimated_cyclomatic_complexity", 0) - 10))

    return {
        "language": "python",
        "quality_score": quality_score,
        "issues": issues,
        "metrics": metrics,
    }


def naive_optimize_python(code: str) -> Dict[str, Any]:
    """Very light optimization/refactor suggestions. Non-destructive."""
    changes: List[str] = []
    optimized = code

    # Strip trailing spaces
    before = optimized
    optimized = "\n".join(line.rstrip() for line in optimized.splitlines())
    if optimized != before:
        changes.append("Removed trailing whitespace")

    # Replace double quotes with single quotes when safe (simple heuristic)
    # Keep it conservative to avoid breaking triple-quoted strings
    if '"' in optimized and "'''" not in optimized and '"""' not in optimized:
        maybe = optimized.replace('"', "'")
        if maybe != optimized:
            optimized = maybe
            changes.append("Normalized quotes to single quotes")

    report = {
        "improvements_made": len(changes),
        "changes": changes,
        "before_size": len(code),
        "after_size": len(optimized),
        "reduction_percent": round((1 - len(optimized) / len(code), 4)[1] * 100 if len(code) else 0, 2),
    }
    return {"optimized_code": optimized, "report": report}


# --- Root/health ---
@app.get("/")
def root():
    return {
        "message": "MARVIN backend is running",
        "version": "1.1.0",
        "storage": str(BASE_STORAGE),
        "endpoints": ["/create", "/upload", "/analyze", "/optimize", "/health"],
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MARVIN API",
        "storage_writable": os.access(BASE_STORAGE, os.W_OK),
        "timestamp": int(time.time()),
    }


# --- Endpoints ---
@app.post("/create")
async def create_file(request: CreateFileRequest):
    try:
        language = request.language or detect_language_from_name(request.filename)
        rel_path = request.filename
        target = FILES_DIR / rel_path
        info = safe_write_file(target, request.content.encode("utf-8"))
        return {
            "status": "success",
            "message": f"Created {rel_path}",
            "data": {
                "filename": rel_path,
                "language": language,
                **info,
            },
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        filename = file.filename
        if not filename or not any(filename.endswith(f".{ext}") for ext in ALLOWED_EXTS):
            raise HTTPException(status_code=400, detail="Unsupported or missing file extension")

        content = await file.read()
        language = detect_language_from_name(filename)

        # Write to storage with content-based name to avoid collisions
        digest = sha256_bytes(content)[:12]
        safe_name = f"{Path(filename).stem}.{digest}.{Path(filename).suffix.lstrip('.')}"
        target = FILES_DIR / safe_name
        info = safe_write_file(target, content)

        return {
            "status": "success",
            "message": f"Uploaded {filename}",
            "data": {
                "original_filename": filename,
                "stored_filename": safe_name,
                "language": language,
                **info,
                "content_type": file.content_type,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_code(request: CodeRequest):
    try:
        language = (request.language or detect_language_from_name(request.filename or "")).lower()
        code = request.code or ""

        if language in ("python", "py", ""):
            analysis = analyze_python(code)
        else:
            # Generic analysis fallback
            lines = code.splitlines()
            non_empty = [l for l in lines if l.strip()]
            analysis = {
                "language": language or "plain",
                "quality_score": 80 if len(code) > 0 else 0,
                "issues": [],
                "metrics": {
                    "total_lines": len(lines),
                    "code_lines": len(non_empty),
                    "blank_lines": len(lines) - len(non_empty),
                },
            }

        # Persist analysis report (optional)
        out_name = f"{(request.filename or 'snippet').replace('/', '_')}.analysis.json"
        out_path = ANALYSIS_DIR / out_name
        safe_write_file(out_path, json.dumps(analysis, indent=2).encode("utf-8"))

        return {
            "status": "success",
            "message": f"Analysis completed for {request.filename or 'snippet'}",
            "data": {
                "filename": request.filename,
                "language": analysis.get("language"),
                "analysis": analysis,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize")
async def optimize_code(request: CodeRequest):
    try:
        language = (request.language or detect_language_from_name(request.filename or "")).lower()
        code = request.code or ""

        if language in ("python", "py", ""):
            result = naive_optimize_python(code)
        else:
            # Placeholder for other languages: no-op but still structured
            result = {"optimized_code": code, "report": {"improvements_made": 0, "changes": [], "before_size": len(code), "after_size": len(code), "reduction_percent": 0.0}}

        return {
            "status": "success",
            "message": f"Optimization completed for {request.filename or 'snippet'}",
            "data": {
                "filename": request.filename,
                "language": language or "plain",
                **result,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
