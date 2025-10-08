from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("")
def upload_file(file: UploadFile):
    # Demo-only: pretend to upload a file and return a message
    if not file.filename:
        raise HTTPException(status_code=400, detail="file is required")
    return {"status": "success", "action": "upload", "filename": file.filename, "size": file.size}
