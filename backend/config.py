"""
Configuration management with .env support and JSON file persistence.
"""
import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# Base directory paths
BASE_DIR = Path(__file__).parent
FIRMWARE_DIR = BASE_DIR / "firmware"
DATABASE_PATH = BASE_DIR / "ota_server.db"
CONFIG_JSON_PATH = BASE_DIR / "config.json"

# Ensure firmware directory exists
FIRMWARE_DIR.mkdir(exist_ok=True)


class MqttSettings(BaseSettings):
    """MQTT broker settings loaded from .env file."""
    mqtt_url: str = Field(default="localhost", alias="MQTT_URL")
    mqtt_port: int = Field(default=1883, alias="MQTT_PORT")
    mqtt_username: Optional[str] = Field(default=None, alias="MQTT_USERNAME")
    mqtt_password: Optional[str] = Field(default=None, alias="MQTT_PASSWORD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class MqttConfig(BaseModel):
    """MQTT configuration model for API responses."""
    broker_url: str
    broker_port: int
    username: Optional[str] = None
    # password is excluded from API responses for security
    
    class Config:
        json_schema_extra = {
            "example": {
                "broker_url": "localhost",
                "broker_port": 1883,
                "username": "mqtt_user"
            }
        }


class MqttConfigUpdate(BaseModel):
    """MQTT configuration update model for API requests."""
    broker_url: str
    broker_port: int
    username: Optional[str] = None
    password: Optional[str] = None


# Global settings instance
settings = MqttSettings()


def load_config_from_json() -> Optional[MqttConfigUpdate]:
    """Load MQTT config from config.json if it exists."""
    if CONFIG_JSON_PATH.exists():
        try:
            with open(CONFIG_JSON_PATH, "r") as f:
                data = json.load(f)
                return MqttConfigUpdate(**data)
        except (json.JSONDecodeError, Exception):
            pass
    return None


def save_config_to_json(config: MqttConfigUpdate) -> None:
    """Save MQTT config to config.json."""
    with open(CONFIG_JSON_PATH, "w") as f:
        json.dump(config.model_dump(), f, indent=2)


def get_effective_config() -> MqttConfigUpdate:
    """Get effective MQTT config (JSON overrides .env)."""
    # Start with .env values
    config = MqttConfigUpdate(
        broker_url=settings.mqtt_url,
        broker_port=settings.mqtt_port,
        username=settings.mqtt_username,
        password=settings.mqtt_password
    )
    
    # Override with JSON file values if exists
    json_config = load_config_from_json()
    if json_config:
        if json_config.broker_url:
            config.broker_url = json_config.broker_url
        if json_config.broker_port:
            config.broker_port = json_config.broker_port
        if json_config.username is not None:
            config.username = json_config.username
        if json_config.password is not None:
            config.password = json_config.password
    
    return config