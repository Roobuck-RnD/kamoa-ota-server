"""
Device CRUD endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import List

from ..storage import get_all_devices, get_device, Device

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/", response_model=List[Device])
def list_devices():
    """List all devices with current status."""
    return get_all_devices()


@router.get("/{device_id}", response_model=Device)
def get_device_by_id(device_id: str):
    """Get single device details by ID."""
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device