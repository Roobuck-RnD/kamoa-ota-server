"""
OTA queue and update endpoints.

Provides API endpoints for managing the OTA update queue:
- Add devices to the update queue
- List and retrieve queue items
- Remove items from queue
- Update queue item status
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

router = APIRouter(prefix="/api/ota", tags=["ota"])


class OtaQueueRequest(BaseModel):
    """Request model for adding a device to the OTA queue.
    
    Attributes:
        device_id: Unique identifier of the device to update.
        firmware_filename: Name of the firmware file to install.
    """
    device_id: str
    firmware_filename: str


class OtaQueueStatusUpdate(BaseModel):
    """Request model for updating queue item status.
    
    Attributes:
        status: New status (pending, in_progress, completed, failed).
        error_message: Optional error message for failed updates.
    """
    status: str
    error_message: Optional[str] = None


@router.post("/queue")
def add_to_ota_queue(request: OtaQueueRequest):
    """
    Add a device to the OTA update queue.
    
    Creates a new queue item with "pending" status. The device will
    receive an OTA command when it sends "ready" status via MQTT.
    
    Args:
        request: OtaQueueRequest with device_id and firmware_filename.
        
    Returns:
        OtaQueueItem: The newly created queue item.
        
    Raises:
        HTTPException: 404 if device not found.
    """
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


@router.get("/queue", response_model=List[OtaQueueItem])
def list_queue_items():
    """
    List all OTA queue items.
    
    Returns:
        List[OtaQueueItem]: All items in the OTA queue.
    """
    return get_all_queue_items()


@router.get("/queue/{queue_id}", response_model=OtaQueueItem)
def get_queue_item_by_id(queue_id: int):
    """
    Get a single queue item by ID.
    
    Args:
        queue_id: The unique ID of the queue item.
        
    Returns:
        OtaQueueItem: The requested queue item.
        
    Raises:
        HTTPException: 404 if queue item not found.
    """
    item = get_queue_item(queue_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return item


@router.delete("/queue/{queue_id}")
def remove_queue_item(queue_id: int):
    """
    Remove an item from the OTA queue.
    
    Args:
        queue_id: The unique ID of the queue item to remove.
        
    Returns:
        dict: Success message.
        
    Raises:
        HTTPException: 404 if queue item not found.
    """
    if not remove_from_queue(queue_id):
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return {"message": "Queue item removed successfully"}


@router.patch("/queue/{queue_id}/status")
def update_queue_item_status(queue_id: int, request: OtaQueueStatusUpdate):
    """
    Manually update a queue item's status.
    
    Args:
        queue_id: The unique ID of the queue item.
        request: OtaQueueStatusUpdate with new status and optional error message.
        
    Returns:
        OtaQueueItem: The updated queue item.
        
    Raises:
        HTTPException: 400 if status is invalid, 404 if item not found.
    """
    if request.status not in ["pending", "in_progress", "completed", "failed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    item = update_queue_status(queue_id, request.status, request.error_message)
    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return item
