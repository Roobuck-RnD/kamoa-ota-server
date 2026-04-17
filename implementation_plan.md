# Implementation Plan

## Overview
This plan addresses 9 issues and feature requests for the IoT OTA Update Server, including configuration loading logic fixes, MQTT reconnection after config changes, firmware deletion, OTA queue UI refactoring, dashboard display improvements, OTA trigger logic corrections, status indicator documentation, code documentation, and README updates.

## Detailed Context

The IoT OTA Update Server is a FastAPI-based application with a vanilla JavaScript frontend that manages over-the-air firmware updates for IoT devices via MQTT. The system consists of:
- Backend: FastAPI with file-based JSON storage
- Frontend: Single-page application with dashboard, settings, firmware, and OTA queue sections
- MQTT: paho-mqtt client for device communication
- WebSocket: Real-time progress updates to connected clients

---

## [Overview]

The implementation addresses configuration persistence issues, UI/UX improvements, and documentation enhancements to make the OTA server more robust and user-friendly.

### Key Issues to Address

1. **Config Loading Logic Bug**: Currently, when the application starts and `config.json` doesn't exist, the code reads from `.env` but immediately saves to `config.json`. This means `.env` is only used once during initial setup, and subsequent `.env` changes are ignored.

2. **MQTT Reconnection**: After updating MQTT configuration via the frontend settings panel, the MQTT client should reconnect with the new credentials. Currently, it only saves the config without reconnecting.

3. **Firmware Deletion**: The firmware management page lacks a delete button to remove uploaded firmware files.

4. **OTA Queue UI**: The current UI uses a dropdown to select devices for adding to the queue. This should be refactored to show all devices in a table with per-device "Add to Queue" and "Remove from Queue" buttons.

5. **Dashboard Display**: The dashboard should show only the operating mode and IP address (not the full topic payload). Firmware version should be extracted from the `device/info` topic payload.

6. **OTA Trigger Logic**: The OTA command should only be sent when a device is in the queue AND sends a "ready" status on the `update/queue/{device_id}` topic.

7. **Status Indicators**: Document what the red/green status indicators mean (MQTT connection, WebSocket connection).

8. **Code Documentation**: Add comprehensive comments and docstrings throughout the codebase.

9. **README Update**: Update the README with accurate information about features, MQTT topics, and usage.

---

## [Types]

New and modified type definitions for the implementation.

### Modified: Device Model (backend/storage.py)

Add new fields to store device information from the `device/info` topic:

```python
class Device(BaseModel):
    device_id: str
    firmware_version: Optional[str] = None
    last_seen: str = ""
    is_online: bool = False
    status: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    # New fields for device info
    ip_address: Optional[str] = None
    operating_mode: Optional[str] = None
    mac_address: Optional[str] = None
    serial_number: Optional[str] = None
```

### New: DeviceInfo Model (backend/storage.py)

```python
class DeviceInfo(BaseModel):
    """Parsed device information from device/info topic."""
    firmwareVersion: Optional[str] = None
    firmwareBuildNumber: Optional[str] = None
    serialNumber: Optional[str] = None
    macAddress: Optional[str] = None
    ipAddress: Optional[str] = None
    dsrcEnabled: Optional[int] = None
    loraEnabled: Optional[int] = None
    bleId: Optional[str] = None
    # ... other fields as needed
```

### New: MqttReconnectResponse (backend/api/config.py)

```python
class MqttReconnectResponse(BaseModel):
    """Response for MQTT reconnection."""
    success: bool
    message: str
    connected: bool
```

### New: FirmwareDeleteResponse (backend/api/firmware.py)

```python
class FirmwareDeleteResponse(BaseModel):
    """Response for firmware deletion."""
    success: bool
    message: str
    filename: str
```

---

## [Files]

Detailed file modifications and new files to be created.

### New Files

1. **backend/api/device_info.py** (NEW)
   - Purpose: Handle device information parsing and storage
   - Contains: Device info parsing logic, API endpoints for device details

### Modified Files

1. **backend/storage.py**
   - Add `ip_address`, `operating_mode` fields to `Device` model
   - Add `delete_firmware` endpoint support (already exists, verify)
   - Add device info parsing functions

2. **backend/mqtt_client.py**
   - Modify `_handle_device_info` to parse the actual payload format
   - Add `reconnect()` method to restart MQTT connection
   - Fix OTA trigger to send to `update/queue/{device_id}` topic

3. **backend/api/config.py**
   - Add `reconnect_mqtt()` endpoint that saves config and triggers reconnection
   - Modify `update_mqtt_config` to return reconnection status

4. **backend/api/firmware.py**
   - Add `DELETE /api/firmware/{filename}` endpoint

5. **backend/api/devices.py**
   - Add `DELETE /api/devices/{device_id}` endpoint (optional, for cleanup)

6. **backend/main.py**
   - Include new device_info router if created
   - Add MQTT reconnection callback

7. **frontend/js/api.js**
   - Add `deleteFirmware(filename)` function
   - Add `reconnectMqtt()` function
   - Add `deleteDevice(deviceId)` function (optional)

8. **frontend/js/settings.js**
   - Modify `saveMqttConfig` to trigger reconnection after save
   - Add loading state during reconnection

9. **frontend/js/dashboard.js**
   - Modify `renderDeviceTable` to show IP and operating mode
   - Update firmware version display to use parsed data

10. **frontend/js/ota.js**
    - Refactor OTA queue UI to show all devices with add/remove buttons
    - Remove device dropdown from OTA controls

11. **frontend/index.html**
    - Update OTA queue section HTML structure
    - Add delete button to firmware table
    - Update dashboard table columns

12. **frontend/css/style.css**
    - Add styles for new UI elements
    - Add delete button styles

13. **README.md**
    - Update feature list
    - Update MQTT topics documentation
    - Add status indicators explanation
    - Update OTA flow documentation

14. **backend/config.py** (optional cleanup)
   - May need to be consolidated with storage.py config handling

---

## [Functions]

Detailed function modifications and new functions.

### New Functions

#### backend/storage.py

1. **`parse_device_info(payload: str) -> DeviceInfo`**
   - Purpose: Parse JSON payload from device/info topic
   - Location: backend/storage.py
   - Returns: Parsed DeviceInfo object

2. **`update_device_from_info(device_id: str, info: DeviceInfo) -> Device`**
   - Purpose: Update device record with parsed info
   - Location: backend/storage.py

#### backend/mqtt_client.py

1. **`reconnect() -> bool`**
   - Purpose: Disconnect and reconnect MQTT client with current config
   - Location: backend/mqtt_client.py
   - Returns: True if reconnection successful

2. **`_handle_device_info(device_id: str, payload: str)`** (MODIFIED)
   - Purpose: Parse device/info topic with correct field names
   - Changes: Use `firmwareVersion` (camelCase) from actual payload

#### backend/api/config.py

1. **`reconnect_mqtt()`**
   - Purpose: Trigger MQTT reconnection after config change
   - Location: backend/api/config.py
   - Endpoint: POST /api/config/mqtt/reconnect

#### backend/api/firmware.py

1. **`delete_firmware(filename: str)`**
   - Purpose: Delete firmware file and metadata
   - Location: backend/api/firmware.py
   - Endpoint: DELETE /api/firmware/{filename}

#### frontend/js/api.js

1. **`deleteFirmware(filename)`**
   - Purpose: API call to delete firmware
   - Location: frontend/js/api.js

2. **`reconnectMqtt()`**
   - Purpose: API call to trigger MQTT reconnection
   - Location: frontend/js/api.js

3. **`toggleDeviceInQueue(deviceId, firmwareFilename, inQueue)`**
   - Purpose: Add or remove device from OTA queue
   - Location: frontend/js/api.js

#### frontend/js/settings.js

1. **`saveMqttConfig(event)`** (MODIFIED)
   - Changes: Call `reconnectMqtt()` after successful save
   - Show loading state during reconnection

#### frontend/js/dashboard.js

1. **`renderDeviceTable(devices)`** (MODIFIED)
   - Changes: Display IP address and operating mode columns
   - Remove full status payload display

#### frontend/js/ota.js

1. **`renderDevicesForOta(devices)`**
   - Purpose: Render devices table with add/remove queue buttons
   - Location: frontend/js/ota.js

2. **`toggleDeviceInQueue(deviceId, firmwareFilename)`**
   - Purpose: Handle add/remove from queue button click
   - Location: frontend/js/ota.js

### Modified Functions

#### backend/storage.py

1. **`get_config()`** (MODIFIED)
   - Current behavior: Creates config.json from .env on first run
   - New behavior: Always check .env as fallback, don't overwrite config.json unnecessarily
   - Changes: Remove auto-save to config.json in `_init_config_from_env()`

2. **`_init_config_from_env()`** (MODIFIED)
   - Changes: Only return config from .env, don't save to config.json

#### backend/mqtt_client.py

1. **`send_ota_command(device_id: str, firmware_filename: str)`** (MODIFIED)
   - Current: Sends to `update/queue/{device_id}` with JSON payload
   - Required: Send HTTP URL to firmware (e.g., `http://server/firmware/file.bin`)
   - Changes: Construct full firmware URL and send as plain text

2. **`_handle_device_status()`** (MODIFIED)
   - Changes: Check for "ready" status on `update/queue/{device_id}` topic specifically

---

## [Classes]

Class modifications for the implementation.

### Modified: MqttClient (backend/mqtt_client.py)

Add methods:
- `reconnect()`: Disconnect and reconnect with current config
- Modify `send_ota_command()` to send HTTP URL instead of JSON

### Modified: Device (backend/storage.py)

Add fields:
- `ip_address: Optional[str]`
- `operating_mode: Optional[str]`
- `mac_address: Optional[str]`

---

## [Dependencies]

No new dependencies required. All changes use existing packages:
- FastAPI (backend)
- paho-mqtt (MQTT client)
- pydantic (data models)
- Vanilla JavaScript (frontend)

---

## [Testing]

Testing approach for each feature.

### Unit Tests (if test framework exists)

1. **Config Loading Tests**
   - Test `.env` fallback when `config.json` missing
   - Test `config.json` takes precedence over `.env`

2. **MQTT Reconnection Tests**
   - Test `reconnect()` method creates new connection
   - Test config is reloaded before reconnect

3. **Device Info Parsing Tests**
   - Test parsing of actual device/info payload format
   - Test extraction of firmwareVersion, ipAddress, etc.

### Manual Testing Checklist

1. **Configuration**
   - [ ] Start server with only `.env` file - should work
   - [ ] Change `.env` and restart - changes should be picked up
   - [ ] Update config via UI - should save and reconnect MQTT
   - [ ] Verify MQTT status indicator updates after reconnection

2. **Firmware Management**
   - [ ] Upload firmware file
   - [ ] Click delete button - file should be removed
   - [ ] Verify file removed from filesystem and index

3. **OTA Queue**
   - [ ] View devices table on OTA page
   - [ ] Click "Add to Queue" - device added to queue
   - [ ] Button changes to "Remove from Queue"
   - [ ] Click "Remove from Queue" - device removed

4. **Dashboard**
   - [ ] Device table shows IP address column
   - [ ] Device table shows operating mode column
   - [ ] Firmware version comes from device/info topic

5. **OTA Trigger**
   - [ ] Device in queue sends "ready" on update/queue/{id}
   - [ ] Server sends HTTP URL to device
   - [ ] Progress updates via WebSocket

---

## [Implementation Order]

Step-by-step implementation sequence to minimize conflicts.

### Phase 1: Configuration Fixes (Tasks 1 & 2)

1. **Fix config loading logic in `backend/storage.py`**
   - Modify `_init_config_from_env()` to not auto-save
   - Modify `get_config()` to use `.env` as true fallback

2. **Add MQTT reconnection functionality**
   - Add `reconnect()` method to `MqttClient` class
   - Add `POST /api/config/mqtt/reconnect` endpoint
   - Update frontend `saveMqttConfig()` to trigger reconnection

### Phase 2: Firmware Deletion (Task 3)

3. **Add delete firmware endpoint**
   - Add `DELETE /api/firmware/{filename}` to `backend/api/firmware.py`
   - Add `deleteFirmware()` to `frontend/js/api.js`

4. **Update firmware UI**
   - Add delete button to firmware table in `frontend/index.html`
   - Add delete handler in `frontend/js/ota.js`

### Phase 3: OTA Queue Refactor (Task 4)

5. **Refactor OTA queue UI**
   - Modify `frontend/index.html` OTA section
   - Create devices table with add/remove buttons
   - Remove device dropdown

6. **Update OTA JavaScript**
   - Modify `frontend/js/ota.js` to handle new UI
   - Add `toggleDeviceInQueue()` function

### Phase 4: Dashboard Improvements (Task 5)

7. **Update device info parsing**
   - Modify `_handle_device_info()` in `backend/mqtt_client.py`
   - Parse `firmwareVersion`, `ipAddress` from payload
   - Update `Device` model in `backend/storage.py`

8. **Update dashboard display**
   - Modify `renderDeviceTable()` in `frontend/js/dashboard.js`
   - Show IP and operating mode columns

### Phase 5: OTA Trigger Logic (Task 6)

9. **Fix OTA command sending**
   - Modify `send_ota_command()` to send HTTP URL
   - Ensure topic is `update/queue/{device_id}`

### Phase 6: Documentation (Tasks 7, 8, 9)

10. **Add code comments**
    - Add docstrings to all functions
    - Add inline comments for complex logic

11. **Update README**
    - Add status indicators explanation
    - Update MQTT topics documentation
    - Update feature list

12. **Final testing and verification**

---

## Status Indicators Explanation

### Header Status Indicators

The header displays two status indicators (colored dots):

| Indicator | Color | Meaning |
|-----------|-------|---------|
| MQTT Status | Green | Successfully connected to MQTT broker |
| MQTT Status | Red | Disconnected from MQTT broker or connection failed |
| WebSocket Status | Green | WebSocket connection to frontend is active |
| WebSocket Status | Red | WebSocket connection is disconnected |

### Device Status Badges

| Status | Color | Meaning |
|--------|-------|---------|
| Online | Green | Device has recently communicated via MQTT |
| Offline | Red | Device has not communicated recently |
| Ready | Blue | Device is ready for OTA update |
| Pending | Yellow | OTA update is queued, waiting for device |
| In Progress | Cyan | OTA update is currently in progress |
| Completed | Green | OTA update completed successfully |
| Failed | Red | OTA update failed |

---

## MQTT Topics Reference

### Subscribed Topics (Server listens)

| Topic Pattern | Description | Payload Format |
|---------------|-------------|----------------|
| `#` | All topics (wildcard) | Varies |
| `{device_id}/device/info` | Device information | JSON with firmwareVersion, ipAddress, etc. |
| `{device_id}/device/status` | Device operational status | Plain text: "ready", "online", etc. |
| `{device_id}/update/queue` | Device ready for OTA | Plain text: "ready" |
| `{device_id}/update/otaStatus` | OTA progress update | JSON with progress, finished, reason |

### Published Topics (Server sends)

| Topic | Description | Payload |
|-------|-------------|---------|
| `update/queue/{device_id}` | OTA start command | HTTP URL to firmware file |

---

## Notes

- The `config.json` file is stored in `backend/data/config.json`
- The `.env` file is stored in `backend/.env`
- Firmware files are stored in `backend/firmware/`
- Device data is stored in `backend/data/devices.json`
- OTA queue is stored in `backend/data/ota_queue.json`