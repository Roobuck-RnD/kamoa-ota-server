"""
MQTT client for subscribing to device topics and publishing OTA commands.
"""
import json
import re
import threading
import time
from typing import Optional, Callable, Dict, Any

import paho.mqtt.client as mqtt

from .storage import (
    update_device_info,
    update_device_status,
    touch_device,
    get_pending_for_device,
    update_queue_status,
    get_firmware_path,
    get_config,
    MqttConfig
)


class MqttClient:
    """Async MQTT client wrapper around paho-mqtt."""
    
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback called when connected to broker."""
        if rc == 0:
            self.connected = True
            print(f"MQTT Connected to broker")
            # Subscribe to all device topics
            client.subscribe("#")
            print("MQTT Subscribed to # (all topics)")
        else:
            print(f"MQTT Connection failed with code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc, properties=None):
        """Callback called when disconnected from broker."""
        self.connected = False
        print(f"MQTT Disconnected (code {rc})")
    
    def on_message(self, client, userdata, msg):
        """Callback called when a message is received."""
        topic = msg.topic
        payload = msg.payload.decode('utf-8') if isinstance(msg.payload, bytes) else str(msg.payload)
        
        print(f"MQTT Received on {topic}: {payload}")
        
        # Parse topic to extract device_id
        parsed = self._parse_device_topic(topic)
        if not parsed:
            return
        
        device_id, topic_type = parsed
        
        # Handle different topic types
        if topic_type == "device/info":
            self._handle_device_info(device_id, payload)
        elif topic_type == "device/status":
            self._handle_device_status(device_id, payload)
        elif topic_type == "ota/response":
            self._handle_ota_response(device_id, payload)
        else:
            # Generic touch for any device topic
            touch_device(device_id)
    
    def _parse_device_topic(self, topic: str) -> Optional[tuple]:
        """
        Parse topic like '0c8b95b851a4/device/info' -> ('0c8b95b851a4', 'device/info')
        Pattern: {device_id}/{topic_type}
        """
        # Match patterns like: device_id/topic or device_id/topic/subtopic
        match = re.match(r'^([^/]+)/(.+)$', topic)
        if match:
            return match.group(1), match.group(2)
        return None
    
    def _handle_device_info(self, device_id: str, payload: str):
        """Handle device/info topic - update firmware version."""
        try:
            data = json.loads(payload)
            firmware_version = data.get("firmware_version") or data.get("version")
            update_device_info(device_id, firmware_version=firmware_version)
            print(f"Device {device_id} info updated: firmware={firmware_version}")
        except json.JSONDecodeError:
            # Try to parse as plain text version
            update_device_info(device_id, firmware_version=payload.strip())
    
    def _handle_device_status(self, device_id: str, payload: str):
        """Handle device/status topic - update status and check for OTA."""
        status = payload.strip().lower()
        update_device_status(device_id, status)
        print(f"Device {device_id} status: {status}")
        
        # Check if device is ready for OTA and has pending update
        if status == "ready":
            self._check_and_trigger_ota(device_id)
    
    def _handle_ota_response(self, device_id: str, payload: str):
        """Handle OTA response from device."""
        try:
            data = json.loads(payload)
            response_type = data.get("type", "")
            queue_item = get_pending_for_device(device_id)
            
            if response_type == "ota_complete" and queue_item:
                update_queue_status(queue_item.id, "completed")
                print(f"Device {device_id} OTA completed")
            elif response_type == "ota_failed" and queue_item:
                error = data.get("error", "Unknown error")
                update_queue_status(queue_item.id, "failed", error)
                print(f"Device {device_id} OTA failed: {error}")
        except json.JSONDecodeError:
            pass
    
    def _check_and_trigger_ota(self, device_id: str):
        """Check if device has pending OTA and trigger it."""
        queue_item = get_pending_for_device(device_id)
        if queue_item:
            print(f"Device {device_id} is ready for OTA, triggering update...")
            update_queue_status(queue_item.id, "in_progress")
            self.send_ota_command(device_id, queue_item.firmware_filename)
    
    def send_ota_command(self, device_id: str, firmware_filename: str):
        """Send OTA start command to device."""
        command = {
            "type": "ota_start",
            "firmware": firmware_filename,
            "timestamp": time.time()
        }
        topic = f"{device_id}/ota/command"
        self.publish(topic, json.dumps(command), qos=1)
        print(f"Sent OTA command to {device_id}: {firmware_filename}")
    
    def publish(self, topic: str, payload: str, qos: int = 0):
        """Publish message to topic."""
        if self.client and self.connected:
            try:
                self.client.publish(topic, payload, qos=qos)
            except Exception as e:
                print(f"MQTT Publish error: {e}")
    
    def connect(self):
        """Connect to MQTT broker."""
        config = get_config()
        
        self.client = mqtt.Client(
            client_id="ota-server",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            userdata=None
        )
        
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Set credentials if provided
        if config.username:
            self.client.username_pw_set(config.username, password=config.password or "")
        
        try:
            self.client.connect(config.broker_url, config.broker_port, keepalive=60)
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            print(f"MQTT Client started, connecting to {config.broker_url}:{config.broker_port}")
        except Exception as e:
            print(f"MQTT Connection error: {e}")
            self.connected = False
    
    def _loop(self):
        """Main MQTT loop in separate thread."""
        while self._running:
            try:
                self.client.loop(timeout=1.0)
            except Exception as e:
                print(f"MQTT Loop error: {e}")
                time.sleep(1)
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self._running = False
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
        self.connected = False
        print("MQTT Client stopped")
    
    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        if self.client and self.connected:
            self.client.subscribe(topic)
    
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self.connected


# Global MQTT client instance
mqtt_client = MqttClient()