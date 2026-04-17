"""
MQTT client for subscribing to device topics and publishing OTA commands.
"""
import json
import os
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
    get_firmware_metadata,
    get_queue_item,
    MqttConfig,
    update_ota_progress,
    clear_ota_progress,
    get_all_queue_items,
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
        
        # print(f"MQTT Received on {topic}: {payload}")
        
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
        elif topic_type == "update/queue":
            self._handle_device_ready(device_id, payload)
        elif topic_type == "ota/response":
            self._handle_ota_response(device_id, payload)
        elif topic_type == "update/otaStatus":
            self._handle_ota_progress(device_id, payload)
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
        """
        Handle device/info topic - parse and store device information.
        
        Parses JSON payload from device/info topic which contains device metadata
        like firmware version, IP address, MAC address, etc.
        
        Expected payload format (camelCase from device):
        {
            "firmwareVersion": "1.2.3",
            "firmwareBuildNumber": "456",
            "ipAddress": "192.168.1.100",
            "macAddress": "00:11:22:33:44:55",
            "serialNumber": "SN123456",
            "operatingMode": "normal"
        }
        """
        try:
            data = json.loads(payload)
            # Parse camelCase fields from device payload
            firmware_version = data.get("firmwareVersion") or data.get("firmware_version") or data.get("version")
            ip_address = data.get("ipAddress") or data.get("ip_address")
            mac_address = data.get("macAddress") or data.get("mac_address")
            serial_number = data.get("serialNumber") or data.get("serial_number")
            operating_mode = data.get("operatingMode") or data.get("operating_mode")
            
            # Update device with all available info
            device = update_device_info(device_id, firmware_version=firmware_version)
            
            # Update additional fields if available
            if device:
                if ip_address:
                    device.ip_address = ip_address
                if mac_address:
                    device.mac_address = mac_address
                if serial_number:
                    device.serial_number = serial_number
                if operating_mode:
                    device.operating_mode = operating_mode
                # Save updated device
                from .storage import save_device
                save_device(device)
            
            print(f"Device {device_id} info updated: firmware={firmware_version}, ip={ip_address}, mode={operating_mode}")
        except json.JSONDecodeError:
            # Try to parse as plain text version
            update_device_info(device_id, firmware_version=payload.strip())

    def _handle_device_ready(self, device_id: str, payload: str):
        """Handle update/queue topic - update status and check for OTA."""
        status = payload.strip().lower()
        
        # Check if device is ready for OTA and has pending update
        if status == "ready":
            print("\n\nREDY TO OTA\n\n")
            self._check_and_trigger_ota(device_id)
    
    def _handle_device_status(self, device_id: str, payload: str):
        """Handle device/status topic - update status and check for OTA."""
        status = payload.strip().lower()
        update_device_status(device_id, status)
        # print(f"Device {device_id} status: {status}")
        
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
    
    def _handle_ota_progress(self, device_id: str, payload: str):
        """Handle OTA progress updates from device on {device_id}/update/otaStatus topic."""
        try:
            data = json.loads(payload)
            progress = data.get("progress", 0)
            finished = data.get("finished", 0)
            reason = data.get("reason", "progress")
            
            # Find the queue item for this device to get firmware filename
            queue_item = None
            all_items = get_all_queue_items()
            for item in all_items:
                if item.device_id == device_id and item.status in ("pending", "in_progress"):
                    queue_item = item
                    break
            
            if not queue_item:
                print(f"No queue item found for device {device_id}")
                return
            
            # Get firmware size from metadata
            firmware_metadata = get_firmware_metadata(queue_item.firmware_filename)
            if not firmware_metadata:
                print(f"No firmware metadata found for {queue_item.firmware_filename}")
                return
            
            # Update progress in storage
            ota_progress = update_ota_progress(
                device_id=device_id,
                queue_id=queue_item.id,
                progress=progress,
                finished=finished,
                reason=reason,
                firmware_filename=queue_item.firmware_filename,
                firmware_size=firmware_metadata.size
            )
            
            print(f"OTA Progress: {device_id} - {ota_progress.percentage:.1f}% ({progress}/{firmware_metadata.size} bytes) - {reason}")
            
            # Broadcast to WebSocket clients
            self._broadcast_ota_progress(ota_progress)
            
            # If finished, update queue status
            if finished == 1:
                update_queue_status(queue_item.id, "completed")
                clear_ota_progress(device_id)
                print(f"Device {device_id} OTA finished")
                
        except json.JSONDecodeError:
            print(f"Invalid JSON in OTA progress message: {payload}")
        except Exception as e:
            print(f"Error handling OTA progress: {e}")
    
    def _broadcast_ota_progress(self, ota_progress):
        """Broadcast OTA progress update to WebSocket clients."""
        try:
            from .websocket_manager import websocket_manager
            import asyncio
            
            message = {
                "type": "ota_progress",
                "device_id": ota_progress.device_id,
                "queue_id": ota_progress.queue_id,
                "progress": ota_progress.progress,
                "finished": ota_progress.finished,
                "reason": ota_progress.reason,
                "percentage": ota_progress.percentage,
                "firmware_filename": ota_progress.firmware_filename,
                "firmware_size": ota_progress.firmware_size,
                "timestamp": ota_progress.timestamp
            }
            
            # Run async broadcast in a thread-safe way
            loop = asyncio.new_event_loop()
            loop.run_until_complete(websocket_manager.broadcast(message))
            loop.close()
            
        except Exception as e:
            print(f"Error broadcasting OTA progress: {e}")
    
    def _check_and_trigger_ota(self, device_id: str):
        """Check if device has pending OTA and trigger it."""
        queue_item = get_pending_for_device(device_id)
        if queue_item:
            print(f"Device {device_id} is ready for OTA, triggering update...")
            update_queue_status(queue_item.id, "in_progress")
            self.send_ota_command(device_id, queue_item.firmware_filename)
    
    def send_ota_command(self, device_id: str, firmware_filename: str):
        """
        Send OTA start command to device.
        
        Sends an HTTP URL to the device pointing to the firmware file location.
        The device will download the firmware from this URL.
        
        Args:
            device_id: The target device identifier.
            firmware_filename: Name of the firmware file to send.
        """
        # Construct HTTP URL to firmware file
        # Using localhost:8000 as the server address (adjustable via environment)
        server_url = os.environ.get("SERVER_URL", "http://localhost:8000")
        command = f"{server_url}/firmware/{firmware_filename}"
        topic = f"update/queue/{device_id}"
        self.publish(topic, command, qos=1)
        print(f"Sent OTA command to {device_id}: {command}")
    
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
    
    def reconnect(self) -> bool:
        """
        Disconnect and reconnect to MQTT broker with current configuration.
        
        This method stops the current MQTT connection, reloads the configuration,
        and establishes a new connection. Useful after configuration changes.
        
        Returns:
            bool: True if reconnection was successful, False otherwise.
        """
        print("MQTT Reconnecting with new configuration...")
        
        # Stop current connection
        self.disconnect()
        
        # Small delay to ensure clean shutdown
        time.sleep(0.5)
        
        # Reconnect with current config
        try:
            self.connect()
            # Wait briefly to check connection status
            time.sleep(1)
            return self.connected
        except Exception as e:
            print(f"MQTT Reconnection failed: {e}")
            return False


# Global MQTT client instance
mqtt_client = MqttClient()
