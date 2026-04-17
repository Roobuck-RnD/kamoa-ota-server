"""
File-based JSON storage for devices, OTA queue, and firmware metadata.
"""
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FIRMWARE_DIR = BASE_DIR / "firmware"
CONFIG_FILE = DATA_DIR / "config.json"
DEVICES_FILE = DATA_DIR / "devices.json"
OTA_QUEUE_FILE = DATA_DIR / "ota_queue.json"
FIRMWARE_INDEX_FILE = DATA_DIR / "firmware_index.json"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
FIRMWARE_DIR.mkdir(exist_ok=True)


def _load_json(filepath: Path, default: Any = None) -> Any:
    """Load JSON from file, return default if not exists."""
    if filepath.exists():
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            pass
    return default


def _save_json(filepath: Path, data: Any) -> None:
    """Save data as JSON to file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _now_iso() -> str:
    """Return current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


# ==================== Device Storage ====================

class Device(BaseModel):
    device_id: str
    firmware_version: Optional[str] = None
    last_seen: str = ""
    is_online: bool = False
    status: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


def get_all_devices() -> List[Device]:
    """Get all devices."""
    data = _load_json(DEVICES_FILE, {})
    return [Device(**d) for d in data.values()]


def get_device(device_id: str) -> Optional[Device]:
    """Get a single device by ID."""
    data = _load_json(DEVICES_FILE, {})
    if device_id in data:
        return Device(**data[device_id])
    return None


def save_device(device: Device) -> None:
    """Save or update a device."""
    data = _load_json(DEVICES_FILE, {})
    data[device.device_id] = device.model_dump()
    _save_json(DEVICES_FILE, data)


def update_device_info(device_id: str, firmware_version: Optional[str] = None, status: Optional[str] = None) -> Device:
    """Update device info from MQTT message."""
    device = get_device(device_id)
    now = _now_iso()
    
    if device is None:
        device = Device(
            device_id=device_id,
            firmware_version=firmware_version,
            last_seen=now,
            is_online=True,
            status=status,
            created_at=now,
            updated_at=now
        )
    else:
        if firmware_version is not None:
            device.firmware_version = firmware_version
        if status is not None:
            device.status = status
        device.last_seen = now
        device.is_online = True
        device.updated_at = now
    
    save_device(device)
    return device


def update_device_status(device_id: str, status: str) -> Optional[Device]:
    """Update device status only."""
    device = get_device(device_id)
    if device:
        device.status = status
        device.last_seen = _now_iso()
        device.is_online = True
        device.updated_at = _now_iso()
        save_device(device)
    return device


def touch_device(device_id: str) -> None:
    """Update last_seen timestamp (keep-alive)."""
    device = get_device(device_id)
    if device:
        device.last_seen = _now_iso()
        device.is_online = True
        device.updated_at = _now_iso()
        save_device(device)


# ==================== OTA Queue Storage ====================

class OtaQueueItem(BaseModel):
    id: int
    device_id: str
    firmware_filename: str
    status: str  # pending, in_progress, completed, failed
    created_at: str
    updated_at: str
    error_message: Optional[str] = None


def get_all_queue_items() -> List[OtaQueueItem]:
    """Get all OTA queue items."""
    data = _load_json(OTA_QUEUE_FILE, [])
    return [OtaQueueItem(**d) for d in data]


def get_queue_item(queue_id: int) -> Optional[OtaQueueItem]:
    """Get a single queue item by ID."""
    items = get_all_queue_items()
    for item in items:
        if item.id == queue_id:
            return item
    return None


def add_to_queue(device_id: str, firmware_filename: str) -> OtaQueueItem:
    """Add a new item to the OTA queue."""
    items = get_all_queue_items()
    new_id = max([i.id for i in items], default=0) + 1
    now = _now_iso()
    
    item = OtaQueueItem(
        id=new_id,
        device_id=device_id,
        firmware_filename=firmware_filename,
        status="pending",
        created_at=now,
        updated_at=now
    )
    
    items.append(item)
    _save_json(OTA_QUEUE_FILE, items)
    return item


def update_queue_status(queue_id: int, status: str, error_message: Optional[str] = None) -> Optional[OtaQueueItem]:
    """Update queue item status."""
    items = _load_json(OTA_QUEUE_FILE, [])
    for i, item in enumerate(items):
        if item["id"] == queue_id:
            items[i]["status"] = status
            items[i]["updated_at"] = _now_iso()
            if error_message:
                items[i]["error_message"] = error_message
            _save_json(OTA_QUEUE_FILE, items)
            return OtaQueueItem(**items[i])
    return None


def remove_from_queue(queue_id: int) -> bool:
    """Remove item from queue."""
    items = _load_json(OTA_QUEUE_FILE, [])
    original_len = len(items)
    items = [i for i in items if i["id"] != queue_id]
    if len(items) < original_len:
        _save_json(OTA_QUEUE_FILE, items)
        return True
    return False


def get_pending_for_device(device_id: str) -> Optional[OtaQueueItem]:
    """Get pending queue item for a device."""
    items = get_all_queue_items()
    for item in items:
        if item.device_id == device_id and item.status == "pending":
            return item
    return None


# ==================== Firmware Storage ====================

class FirmwareMetadata(BaseModel):
    filename: str
    size: int
    uploaded_at: str
    md5_hash: str


def get_firmware_index() -> Dict[str, FirmwareMetadata]:
    """Get firmware index (filename -> metadata)."""
    data = _load_json(FIRMWARE_INDEX_FILE, {})
    return {k: FirmwareMetadata(**v) for k, v in data.items()}


def list_firmware() -> List[FirmwareMetadata]:
    """List all firmware files."""
    return list(get_firmware_index().values())


def get_firmware_metadata(filename: str) -> Optional[FirmwareMetadata]:
    """Get metadata for a firmware file."""
    index = get_firmware_index()
    return index.get(filename)


def save_firmware_file(filename: str, content: bytes) -> FirmwareMetadata:
    """Save firmware binary file and update index."""
    filepath = FIRMWARE_DIR / filename
    md5_hash = hashlib.md5(content).hexdigest()
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    metadata = FirmwareMetadata(
        filename=filename,
        size=len(content),
        uploaded_at=_now_iso(),
        md5_hash=md5_hash
    )
    
    index = get_firmware_index()
    index[filename] = metadata
    _save_json(FIRMWARE_INDEX_FILE, index)
    
    return metadata


def get_firmware_path(filename: str) -> Optional[Path]:
    """Get path to firmware file if exists."""
    filepath = FIRMWARE_DIR / filename
    if filepath.exists():
        return filepath
    return None


def delete_firmware(filename: str) -> bool:
    """Delete firmware file and metadata."""
    filepath = FIRMWARE_DIR / filename
    if filepath.exists():
        filepath.unlink()
    
    index = get_firmware_index()
    if filename in index:
        del index[filename]
        _save_json(FIRMWARE_INDEX_FILE, index)
        return True
    return False


# ==================== Config Storage ====================

class MqttConfig(BaseModel):
    broker_url: str
    broker_port: int
    username: Optional[str] = None
    password: Optional[str] = None


def _init_config_from_env() -> MqttConfig:
    """Initialize config from .env file if config.json doesn't exist."""
    import os
    
    config = MqttConfig(
        broker_url=os.environ.get("MQTT_URL", "localhost"),
        broker_port=int(os.environ.get("MQTT_PORT", "1883")),
        username=os.environ.get("MQTT_USERNAME") or None,
        password=os.environ.get("MQTT_PASSWORD") or None
    )
    
    # Save to config.json for persistence
    save_config(config)
    return config


def get_config() -> MqttConfig:
    """Get MQTT configuration."""
    if not CONFIG_FILE.exists():
        return _init_config_from_env()
    
    data = _load_json(CONFIG_FILE, {
        "broker_url": "localhost",
        "broker_port": 1883,
        "username": None,
        "password": None
    })
    return MqttConfig(**data)


def save_config(config: MqttConfig) -> None:
    """Save MQTT configuration."""
    _save_json(CONFIG_FILE, config.model_dump())
