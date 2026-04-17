# Implementation Plan

[Overview]
Build a complete IoT OTA (Over-The-Air) update management system with a FastAPI backend and vanilla JavaScript SPA frontend, containerized with Docker Compose.

This system provides a dashboard to monitor approximately 30 IoT devices, receive their status updates via MQTT, manage firmware files, and trigger OTA updates based on device readiness. The backend subscribes to MQTT topics to track device information and status, stores device data in SQLite, and exposes REST APIs for the frontend. The frontend is a simple single-page application built with vanilla HTML, CSS, and JavaScript that displays device information, allows configuration of MQTT settings, and enables firmware upload and OTA update triggering.

The architecture follows a clean separation of concerns: MQTT client handles broker communication, REST API endpoints serve the frontend, SQLite stores persistent data, and a simple in-memory queue manages OTA update requests.

[Types]

The system uses the following data structures and types:

**Device Model**
- `device_id` (string, primary key): Unique device identifier extracted from MQTT topic (e.g., "0c8b95b851a4")
- `firmware_version` (string, nullable): Current firmware version from device/info topic
- `last_seen` (datetime): Timestamp of last received message
- `is_online` (boolean): Whether device is currently online
- `status` (string, nullable): Current status message (e.g., "ready" for OTA)
- `created_at` (datetime): When device was first discovered
- `updated_at` (datetime): Last update timestamp

**OtaQueue Model**
- `id` (integer, primary key): Auto-increment ID
- `device_id` (string, foreign key): Reference to device
- `firmware_filename` (string): Name of firmware file to upload
- `status` (string): "pending", "in_progress", "completed", "failed"
- `created_at` (datetime): When queued
- `updated_at` (datetime): Last status update
- `error_message` (string, nullable): Error details if failed

**MqttConfig Model**
- `broker_url` (string): MQTT broker hostname/IP
- `broker_port` (integer): MQTT broker port (default 1883)
- `username` (string, nullable): MQTT username
- `password` (string, nullable): MQTT password

**Firmware File**
- `filename` (string): Original uploaded filename
- `size` (integer): File size in bytes
- `uploaded_at` (datetime): Upload timestamp
- `md5_hash` (string): MD5 checksum for integrity verification

[Files]

**New Files to be Created:**

Backend:
- `backend/main.py` - FastAPI application entry point with all routes
- `backend/config.py` - Configuration management with .env support
- `backend/mqtt_client.py` - MQTT client for subscribing and publishing
- `backend/database.py` - SQLite database setup and session management
- `backend/models.py` - SQLAlchemy ORM models (Device, OtaQueue, MqttConfig)
- `backend/api/devices.py` - Device CRUD endpoints
- `backend/api/ota.py` - OTA queue and update endpoints
- `backend/api/config.py` - MQTT configuration endpoints
- `backend/api/firmware.py` - Firmware upload and download endpoints
- `backend/services/ota_service.py` - OTA update logic and state machine
- `backend/services/device_service.py` - Device management logic
- `backend/.env.example` - Example environment variables

Frontend:
- `frontend/index.html` - Main HTML page
- `frontend/css/style.css` - Stylesheet
- `frontend/js/app.js` - Main application logic
- `frontend/js/api.js` - API client functions
- `frontend/js/dashboard.js` - Dashboard rendering
- `frontend/js/settings.js` - Settings panel logic
- `frontend/js/ota.js` - OTA update logic

Infrastructure:
- `docker-compose.yml` - Docker Compose configuration
- `Dockerfile.backend` - Backend container definition
- `Dockerfile.frontend` - Frontend container definition (nginx)
- `backend/requirements.txt` - Python dependencies
- `backend/firmware/` - Directory for uploaded firmware files

**Existing Files to be Modified:**
None (this is a new project)

**Configuration Files:**
- `backend/.env` - Environment variables (generated from .env.example)
- `backend/config.json` - MQTT configuration (updated via API)

[Functions]

**Backend API Endpoints:**

`GET /api/devices` - List all devices with current status
- Returns: Array of Device objects

`GET /api/devices/{device_id}` - Get single device details
- Returns: Device object

`POST /api/ota/queue` - Add device to OTA update queue
- Body: { "device_id": "string", "firmware_filename": "string" }
- Returns: OtaQueue object

`GET /api/ota/queue` - List OTA queue items
- Returns: Array of OtaQueue objects

`DELETE /api/ota/queue/{queue_id}` - Remove item from OTA queue
- Returns: Success message

`GET /api/config/mqtt` - Get MQTT configuration
- Returns: MqttConfig object (without password)

`POST /api/config/mqtt` - Update MQTT configuration
- Body: { "broker_url": "string", "broker_port": int, "username": "string", "password": "string" }
- Returns: Success message

`POST /api/firmware/upload` - Upload firmware binary file
- Body: multipart/form-data with "file" field
- Returns: { "filename": "string", "size": int, "md5_hash": "string" }

`GET /api/firmware/{filename}` - Download firmware file
- Returns: Binary file

`GET /api/firmware/list` - List available firmware files
- Returns: Array of firmware metadata

`GET /health` - Health check endpoint
- Returns: { "status": "healthy", "mqtt_connected": boolean }

**MQTT Client Functions:**

`MqttClient.__init__(config)` - Initialize MQTT client with configuration
`MqttClient.connect()` - Connect to MQTT broker
`MqttClient.subscribe()` - Subscribe to device topics (#)
`MqttClient.publish(topic, payload, qos=0)` - Publish message to topic
`MqttClient.disconnect()` - Disconnect from broker
`_on_message(topic, payload)` - Handle incoming MQTT messages
`_parse_device_topic(topic)` - Extract device_id and topic_type from topic

**OTA Service Functions:**

`OtaService.process_queue()` - Process pending OTA updates
`OtaService.check_device_ready(device_id)` - Check if device sent "ready" status
`OtaService.send_ota_command(device_id, firmware_info)` - Send OTA start command
`OtaService.handle_ota_response(device_id, status)` - Handle device OTA response
`OtaService.update_queue_status(queue_id, status, error=None)` - Update queue item status

**Frontend Functions:**

`initApp()` - Initialize application
`fetchDevices()` - Fetch and display device list
`renderDeviceTable(devices)` - Render device list as HTML table
`showSettings()` - Show settings panel
`saveMqttConfig(config)` - Save MQTT configuration
`uploadFirmware(file)` - Upload firmware file
`addToOtaQueue(deviceId, firmwareFile)` - Add device to OTA queue
`renderOtaQueue(queue)` - Render OTA queue table
`refreshDevices()` - Refresh device list

[Classes]

**Backend Classes:**

`MqttClient` (backend/mqtt_client.py)
- Purpose: Async MQTT client wrapper around paho-mqtt
- Key methods: connect(), subscribe(), publish(), disconnect()
- Handles: Automatic reconnection, message parsing, topic filtering

`OtaService` (backend/services/ota_service.py)
- Purpose: Manage OTA update workflow and state machine
- Key methods: process_queue(), check_device_ready(), send_ota_command(), handle_ota_response()
- State machine: pending → in_progress → completed/failed

`DeviceService` (backend/services/device_service.py)
- Purpose: Device management and discovery
- Key methods: get_or_create_device(), update_device_info(), update_device_status()

**Database Models (SQLAlchemy):**

`Device` (backend/models.py)
- Fields: device_id, firmware_version, last_seen, is_online, status, created_at, updated_at
- Relationships: One-to-many with OtaQueue

`OtaQueue` (backend/models.py)
- Fields: id, device_id, firmware_filename, status, created_at, updated_at, error_message
- Relationships: Many-to-one with Device

`MqttConfig` (backend/models.py)
- Fields: id (always 1), broker_url, broker_port, username, password

[Dependencies]

**Backend Dependencies (requirements.txt):**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
paho-mqtt==1.6.1
sqlalchemy==2.0.25
aiosqlite==0.19.0
python-dotenv==1.0.1
pydantic==2.5.3
python-multipart==0.0.6
```

**Frontend Dependencies:**
None (vanilla JavaScript, no build tools required)

**Docker:**
- Backend: python:3.11-slim base image
- Frontend: nginx:alpine base image

[Testing]

**Manual Testing Approach:**

1. **MQTT Connection Test:**
   - Verify /health endpoint returns mqtt_connected: true
   - Check logs for successful MQTT subscription

2. **Device Discovery Test:**
   - Publish test message to `{device_id}/device/info` topic
   - Verify device appears in /api/devices response

3. **OTA Flow Test:**
   - Upload firmware file via /api/firmware/upload
   - Add device to queue via /api/ota/queue
   - Verify device receives OTA command when "ready" status is sent
   - Check queue status updates

4. **Configuration Test:**
   - Update MQTT config via /api/config/mqtt
   - Verify config persists in config.json
   - Verify .env values are loaded correctly

**Test Scenarios:**
- Device sends device/info with firmware version
- Device sends device/status with "ready" message
- Device already in queue when ready (should trigger OTA)
- Multiple devices in queue (process one at a time)
- Firmware file upload and download
- MQTT reconnection after broker restart

[Implementation Order]

**Step 1: Backend Foundation**
1. Create `backend/config.py` with Pydantic settings and .env support
2. Create `backend/database.py` with SQLite setup and session management
3. Create `backend/models.py` with SQLAlchemy models (Device, OtaQueue, MqttConfig)
4. Create `backend/requirements.txt` with dependencies

**Step 2: MQTT Client**
5. Create `backend/mqtt_client.py` with MqttClient class
6. Implement topic parsing and message handling
7. Add handlers for device/info and device/status topics

**Step 3: API Endpoints**
8. Create `backend/api/devices.py` with device CRUD endpoints
9. Create `backend/api/config.py` with MQTT config endpoints
10. Create `backend/api/firmware.py` with firmware upload/download endpoints
11. Create `backend/api/ota.py` with OTA queue endpoints

**Step 4: Services**
12. Create `backend/services/device_service.py` for device management
13. Create `backend/services/ota_service.py` for OTA workflow

**Step 5: Main Application**
14. Create `backend/main.py` integrating all components
15. Add startup/shutdown handlers for MQTT client
16. Add background task for OTA queue processing

**Step 6: Frontend**
17. Create `frontend/index.html` with basic structure
18. Create `frontend/css/style.css` with styling
19. Create `frontend/js/api.js` with API client functions
20. Create `frontend/js/app.js` with main application logic
21. Create `frontend/js/dashboard.js` for device list rendering
22. Create `frontend/js/settings.js` for settings panel
23. Create `frontend/js/ota.js` for OTA queue management

**Step 7: Docker Configuration**
24. Create `Dockerfile.backend` for backend container
25. Create `Dockerfile.frontend` for nginx frontend container
26. Create `docker-compose.yml` with both services
27. Create `backend/.env.example` with template variables

**Step 8: Testing and Refinement**
28. Test MQTT connection and device discovery
29. Test firmware upload and download
30. Test OTA queue and update flow
31. Verify frontend functionality
32. Test Docker Compose deployment