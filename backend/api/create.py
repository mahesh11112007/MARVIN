from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/create", tags=["create"])

class CreateRequest(BaseModel):
    filename: str
    content: str = ""

@router.post("")
def create_file(req: CreateRequest):
    # Demo-only: pretend to create a file and return a message
    if not req.filename:
        raise HTTPException(status_code=400, detail="filename is required")
    return {"status": "success", "action": "create", "filename": req.filename, "bytes": len(req.content)}
