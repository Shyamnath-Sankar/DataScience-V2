"""
File management API routes.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import FileRecord, FilePreview, ErrorResponse
from services import file_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileRecord)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or XLSX file."""
    try:
        record = await file_service.upload_file(file)
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[FileRecord])
async def list_files():
    """List all uploaded files."""
    return file_service.list_files()


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file."""
    success = file_service.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found.")
    return {"message": "File deleted."}


@router.get("/{file_id}/preview", response_model=FilePreview)
async def get_preview(file_id: str):
    """Get first 200 rows of a file for grid display."""
    try:
        return file_service.load_preview(file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{file_id}/full")
async def get_full_data(file_id: str):
    """Get full file data."""
    try:
        return file_service.load_full_data(file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
