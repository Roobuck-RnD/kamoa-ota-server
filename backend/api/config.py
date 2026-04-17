"""
MQTT configuration endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..storage import get_config, save_config, MqttConfig

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
    """Update MQTT configuration."""
    new_config = MqttConfig(
        broker_url=config.broker_url,
        broker_port=config.broker_port,
        username=config.username,
        password=config.password
    )
    save_config(new_config)
    return {"message": "Configuration updated successfully"}