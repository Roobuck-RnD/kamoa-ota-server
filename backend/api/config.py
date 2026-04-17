"""
MQTT configuration endpoints.

Provides API endpoints for viewing and updating MQTT broker configuration,
including reconnection after configuration changes.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..storage import get_config, save_config, MqttConfig
from ..mqtt_client import mqtt_client

router = APIRouter(prefix="/api/config/mqtt", tags=["config"])


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


@router.get("/", response_model=MqttConfigResponse)
def get_mqtt_config():
    """Get MQTT configuration (password excluded for security)."""
    config = get_config()
    return MqttConfigResponse(
        broker_url=config.broker_url,
        broker_port=config.broker_port,
        username=config.username
    )


@router.post("/")
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


@router.post("/reconnect", response_model=MqttReconnectResponse)
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
