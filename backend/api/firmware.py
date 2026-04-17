"""
Firmware upload and download endpoints.
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List

from ..storage import (
    save_firmware_file,
    list_firmware,
    get_firmware_path,
    get_firmware_metadata,
    FirmwareMetadata
)

router = APIRouter(prefix="/api/firmware", tags=["firmware"])


@router.post("/upload")
async def upload_firmware(file: UploadFile = File(...)):
    """Upload firmware binary file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Read file content
    content = await file.read()
    
    # Generate unique filename if needed
    filename = file.filename
    base, ext = os.path.splitext(filename)
    counter = 1
    while get_firmware_metadata(filename):
        filename = f"{base}_{counter}{ext}"
        counter += 1
    
    # Save file and get metadata
    metadata = save_firmware_file(filename, content)
    
    return {
        "filename": metadata.filename,
        "size": metadata.size,
        "md5_hash": metadata.md5_hash,
        "uploaded_at": metadata.uploaded_at
    }


@router.get("/list", response_model=List[FirmwareMetadata])
def list_firmware_files():
    """List available firmware files."""
    return list_firmware()


@router.get("/{filename}")
def download_firmware(filename: str):
    """Download firmware file."""
    filepath = get_firmware_path(filename)
    if not filepath:
        raise HTTPException(status_code=404, detail=f"Firmware file {filename} not found")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )