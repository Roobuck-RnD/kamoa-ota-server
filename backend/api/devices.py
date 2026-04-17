"""
Device CRUD endpoints.

Provides API endpoints for device management:
- List all registered devices
- Get individual device details including IP address and operating mode
"""
from fastapi import APIRouter, HTTPException
from typing import List

from ..storage import get_all_devices, get_device, Device

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/", response_model=List[Device])
def list_devices():
    """
    List all registered devices with their current status.
    
    Returns device information including:
    - device_id: Unique identifier
    - firmware_version: Current firmware version
    - ip_address: Device IP address (if available from device/info)
    - operating_mode: Operating mode (if available from device/info)
    - is_online: Current online status
    - last_seen: Last communication timestamp
    - status: Current device status
    
    Returns:
        List[Device]: All registered devices.
    """
    return get_all_devices()


@router.get("/{device_id}", response_model=Device)
def get_device_by_id(device_id: str):
    """
    Get detailed information for a single device.
    
    Args:
        device_id: The unique identifier of the device.
        
    Returns:
        Device: Device details including all available information.
        
    Raises:
        HTTPException: 404 if device not found.
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device
