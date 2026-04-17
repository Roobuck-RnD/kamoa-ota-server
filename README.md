# IoT OTA Update Server

A comprehensive Over-The-Air (OTA) update management system for IoT devices with a FastAPI backend and vanilla JavaScript frontend.

## Features

- **Device Dashboard**: Monitor IoT devices with real-time status, IP address, firmware version, and operating mode
- **MQTT Integration**: Subscribe to device topics for real-time status updates via paho-mqtt
- **Firmware Management**: Upload, download, and delete firmware files with MD5 checksum verification
- **OTA Queue**: Per-device add/remove from update queue with real-time progress tracking
- **Settings Panel**: Configure MQTT broker URL, port, username, and password with automatic reconnection
- **WebSocket Support**: Real-time OTA progress updates pushed to connected clients
- **Status Indicators**: Visual indicators for MQTT and WebSocket connection status

## Architecture

- **Backend**: FastAPI with file-based JSON storage (no database required)
- **Frontend**: Vanilla JavaScript SPA served directly by FastAPI
- **MQTT**: paho-mqtt client for device communication
- **WebSocket**: Real-time progress updates via WebSocket connections
- **Storage**: JSON files for devices, OTA queue, config, and firmware metadata

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- MQTT Broker (e.g., Mosquitto)

### Using Docker Compose (Recommended)

1. Configure MQTT settings in `backend/.env`:
```
MQTT_URL=your-mqtt-broker
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
```

2. Start the server:
```bash
docker-compose up -d
```

3. Access the UI at: http://localhost:8000

### Running Locally

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure MQTT in `backend/.env`

3. Run the server:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Status Indicators

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

## MQTT Topics

### Subscribed Topics (Server listens)

| Topic Pattern | Description | Payload Format |
|---------------|-------------|----------------|
| `#` | All topics (wildcard subscription) | Varies |
| `{device_id}/device/info` | Device information | JSON with `firmwareVersion`, `ipAddress`, `operatingMode`, etc. |
| `{device_id}/device/status` | Device operational status | Plain text: "ready", "online", etc. |
| `{device_id}/update/otaStatus` | OTA progress update | JSON with `progress`, `finished`, `reason` |

### Published Topics (Server sends)

| Topic | Description | Payload |
|-------|-------------|---------|
| `{device_id}/update/queue` | OTA start command | HTTP URL to firmware file (e.g., `http://server:8000/api/firmware/firmware.bin`) |

### Device Info Payload Format

The server expects device/info messages in the following JSON format (camelCase):

```json
{
    "firmwareVersion": "1.2.3",
    "firmwareBuildNumber": "456",
    "ipAddress": "192.168.1.100",
    "macAddress": "00:11:22:33:44:55",
    "serialNumber": "SN123456",
    "operatingMode": "normal"
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/devices | List all devices |
| GET | /api/devices/{id} | Get device by ID |
| GET | /api/config/mqtt | Get MQTT config |
| POST | /api/config/mqtt | Update MQTT config |
| POST | /api/config/mqtt/reconnect | Reconnect MQTT client |
| POST | /api/firmware/upload | Upload firmware file |
| GET | /api/firmware/list | List firmware files |
| GET | /api/firmware/{name} | Download firmware |
| DELETE | /api/firmware/{name} | Delete firmware file |
| GET | /api/ota/queue | List OTA queue |
| POST | /api/ota/queue | Add to OTA queue |
| DELETE | /api/ota/queue/{id} | Remove from queue |
| PATCH | /api/ota/queue/{id}/status | Update queue item status |
| GET | /health | Health check |

## Directory Structure

```
kamoa-ota-server/
├── backend/
│   ├── main.py           # FastAPI application entry point
│   ├── mqtt_client.py    # MQTT client with device info parsing
│   ├── storage.py        # JSON file storage and data models
│   ├── websocket_manager.py # WebSocket connection management
│   ├── api/              # API routers
│   │   ├── devices.py    # Device endpoints
│   │   ├── config.py     # MQTT config endpoints
│   │   ├── firmware.py   # Firmware upload/download/delete
│   │   └── ota.py        # OTA queue management
│   ├── .env              # MQTT configuration (environment variables)
│   ├── data/             # Device/queue JSON files
│   └── firmware/         # Firmware files storage
├── frontend/
│   ├── index.html        # Main HTML file
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       ├── api.js        # API client functions
│       ├── app.js        # Main application logic
│       ├── dashboard.js  # Device table rendering
│       ├── settings.js   # MQTT config panel
│       ├── ota.js        # OTA queue management
│       ├── websocket.js  # WebSocket connection
│       └── toast.js      # Toast notifications
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile.backend    # Backend Docker image
├── nginx.conf            # Nginx reverse proxy config
└── README.md             # This file
```

## OTA Flow

1. User uploads firmware file via UI (stored in `backend/firmware/`)
2. User navigates to OTA Queue page
3. User selects firmware for a device and clicks "Add to Queue"
4. Backend monitors for device sending "ready" on `{device_id}/device/status`
5. When device is ready and in queue, backend sends HTTP URL to `{device_id}/update/queue`
6. Device downloads firmware from the provided URL
7. Device sends progress updates on `{device_id}/update/otaStatus`
8. WebSocket pushes real-time progress to connected frontend clients
9. Queue status updates automatically when OTA completes

## Configuration

### MQTT Settings

MQTT settings can be configured in two ways:

1. **Via `backend/.env` file** (loaded on startup if no config.json exists):
   ```
   MQTT_URL=localhost
   MQTT_PORT=1883
   MQTT_USERNAME=
   MQTT_PASSWORD=
   ```

2. **Via UI Settings panel** (saved to `backend/data/config.json`):
   - Navigate to Settings tab
   - Enter broker URL, port, username, and password
   - Click "Save Configuration" to save and automatically reconnect

### Server URL

The server URL for OTA commands can be configured via environment variable:
```
SERVER_URL=http://localhost:8000
```

This URL is used when constructing the firmware download URL sent to devices.

## Recent Updates

### Version 2.0 (Current)

- **Config Loading Fix**: `.env` changes are now respected on restart when no `config.json` exists
- **MQTT Reconnection**: Automatic reconnection after config changes via UI
- **Firmware Deletion**: Added delete button to remove firmware files
- **OTA Queue UI**: Refactored to show all devices with per-device add/remove queue buttons
- **Dashboard Enhancement**: Added IP address and operating mode columns
- **Device Info Parsing**: Now parses `firmwareVersion`, `ipAddress`, `operatingMode` from device/info topic
- **OTA Command Fix**: Sends HTTP URL instead of JSON payload to devices
- **Comprehensive Documentation**: Added docstrings and code comments throughout

## Troubleshooting

### MQTT Connection Issues

1. Check MQTT broker is running and accessible
2. Verify credentials in Settings panel or `.env` file
3. Check the MQTT status indicator in the header (green = connected, red = disconnected)
4. Use the Settings panel to update credentials and trigger reconnection

### Devices Not Appearing

1. Ensure devices are publishing to `{device_id}/device/info` topic
2. Verify MQTT broker is forwarding messages correctly
3. Check device info payload format matches expected JSON structure

### OTA Not Triggering

1. Ensure device is in the OTA queue
2. Device must send "ready" status on `{device_id}/device/status` topic
3. Check MQTT connection is active (green indicator)

## License

Roobuck Inc. propietary license
