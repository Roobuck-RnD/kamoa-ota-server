"""
MQTT configuration endpoints.

Provides API endpoints for viewing and updating MQTT broker configuration,
including reconnection after configuration changes.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..storage import (
    get_config, 
    save_config, 
    MqttConfig,
    get_firmware_server_config,
    save_firmware_server_config,
    FirmwareServerConfig
)
from ..mqtt_client import mqtt_client

router = APIRouter(prefix="/api/config", tags=["config"])


class MqttConfigResponse(BaseModel):
    """MQTT config response (without password)."""
    broker_url: str
    broker_port: int
    username: Optional[str] = None


class MqttConfigUpdate(BaseModel):
    """MQTT config update request."""
    broker_url: str
    broker_port: int
    username: Optional[str] = None
    password: Optional[str] = None


class MqttReconnectResponse(BaseModel):
    """Response for MQTT reconnection request."""
    success: bool
    message: str
    connected: bool


@router.get("/mqtt", response_model=MqttConfigResponse)
def get_mqtt_config():
    """Get MQTT configuration (password excluded for security)."""
    config = get_config()
    return MqttConfigResponse(
        broker_url=config.broker_url,
        broker_port=config.broker_port,
        username=config.username
    )


@router.post("/mqtt")
def update_mqtt_config(config: MqttConfigUpdate):
    """
    Update MQTT configuration.
    
    Saves new MQTT broker configuration to config.json.
    Does NOT automatically reconnect - call /reconnect endpoint separately.
    """
    new_config = MqttConfig(
        broker_url=config.broker_url,
        broker_port=config.broker_port,
        username=config.username,
        password=config.password
    )
    save_config(new_config)
    return {"message": "Configuration updated successfully"}


@router.post("/mqtt/reconnect", response_model=MqttReconnectResponse)
def reconnect_mqtt():
    """
    Reconnect MQTT client with current configuration.
    
    This endpoint should be called after updating MQTT configuration
    to establish a new connection with the updated settings.
    
    Returns:
        MqttReconnectResponse: Status of the reconnection attempt.
    """
    success = mqtt_client.reconnect()
    return MqttReconnectResponse(
        success=success,
        message="Reconnection successful" if success else "Reconnection failed",
        connected=mqtt_client.is_connected()
    )


# ==================== Firmware Server Config ====================

class FirmwareServerConfigResponse(BaseModel):
    """Firmware server config response."""
    host: str
    port: int
    protocol: str


class FirmwareServerConfigUpdate(BaseModel):
    """Firmware server config update request."""
    host: str
    port: int
    protocol: str = "http"


@router.get("/firmware-server", response_model=FirmwareServerConfigResponse)
def get_firmware_server_config_api():
    """Get firmware server configuration."""
    config = get_firmware_server_config()
    return FirmwareServerConfigResponse(
        host=config.host,
        port=config.port,
        protocol=config.protocol
    )


@router.post("/firmware-server")
def update_firmware_server_config(config: FirmwareServerConfigUpdate):
    """
    Update firmware server configuration.
    
    Validates that host is not localhost before saving.
    """
    # Validate host is not localhost
    host_lower = config.host.lower()
    if host_lower in ("localhost", "127.0.0.1", "::1"):
        raise HTTPException(
            status_code=400,
            detail="Firmware server host cannot be localhost. Please use the actual server IP address."
        )
    
    new_config = FirmwareServerConfig(
        host=config.host,
        port=config.port,
        protocol=config.protocol
    )
    save_firmware_server_config(new_config)
    return {"message": "Firmware server configuration updated successfully"}
