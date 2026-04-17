"""
OTA queue and update endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from ..storage import (
    get_all_queue_items,
    add_to_queue,
    remove_from_queue,
    get_queue_item,
    update_queue_status,
    get_device,
    OtaQueueItem
)

router = APIRouter(prefix="/api/ota/queue", tags=["ota"])


class OtaQueueRequest(BaseModel):
    """Request to add device to OTA queue."""
    device_id: str
    firmware_filename: str


@router.post("/")
def add_to_ota_queue(request: OtaQueueRequest):
    """Add device to OTA update queue."""
    # Verify device exists
    device = get_device(request.device_id)
    if not device:
        raise HTTPException(
            status_code=404,
            detail=f"Device {request.device_id} not found"
        )
    
    # Add to queue
    queue_item = add_to_queue(request.device_id, request.firmware_filename)
    return queue_item


@router.get("/", response_model=List[OtaQueueItem])
def list_queue_items():
    """List all OTA queue items."""
    return get_all_queue_items()


@router.get("/{queue_id}", response_model=OtaQueueItem)
def get_queue_item_by_id(queue_id: int):
    """Get single queue item by ID."""
    item = get_queue_item(queue_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return item


@router.delete("/{queue_id}")
def remove_queue_item(queue_id: int):
    """Remove item from OTA queue."""
    if not remove_from_queue(queue_id):
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return {"message": "Queue item removed successfully"}


@router.patch("/{queue_id}/status")
def update_queue_item_status(queue_id: int, status: str, error_message: Optional[str] = None):
    """Manually update queue item status."""
    if status not in ["pending", "in_progress", "completed", "failed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    item = update_queue_status(queue_id, status, error_message)
    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return item