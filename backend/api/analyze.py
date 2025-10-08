from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/analyze", tags=["analyze"])

class AnalyzeRequest(BaseModel):
    code: str
    language: str = "python"

@router.post("")
def analyze_code(req: AnalyzeRequest):
    # Demo-only: pretend to analyze code and return a message
    if not req.code:
        raise HTTPException(status_code=400, detail="code is required")
    return {"status": "success", "action": "analyze", "language": req.language, "lines": req.code.count('\n') + 1}
