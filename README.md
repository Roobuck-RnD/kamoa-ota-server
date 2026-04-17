# IoT OTA Update Server

A simple Over-The-Air (OTA) update management system for IoT devices with a FastAPI backend and vanilla JavaScript frontend.

## Features

- **Device Dashboard**: Monitor ~30 IoT devices with their status and firmware version
- **MQTT Integration**: Subscribe to device topics for real-time status updates
- **Firmware Management**: Upload and manage firmware files
- **OTA Queue**: Add devices to update queue, automatically triggered when device sends "ready" status
- **Settings Panel**: Configure MQTT broker URL, port, username, and password

## Architecture

- **Backend**: FastAPI with file-based JSON storage (no database required)
- **Frontend**: Vanilla JavaScript SPA served directly by FastAPI
- **MQTT**: paho-mqtt client for device communication
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

## MQTT Topics

The server subscribes to all topics (`#`) and handles:

- `{device_id}/device/info` - Device information (firmware version)
- `{device_id}/device/status` - Device status (e.g., "ready" for OTA)
- `{device_id}/ota/response` - OTA completion/failure responses

When a device sends "ready" status and has a pending OTA in the queue, the server automatically sends an OTA command to `{device_id}/ota/command`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/devices | List all devices |
| GET | /api/devices/{id} | Get device by ID |
| GET | /api/config/mqtt | Get MQTT config |
| POST | /api/config/mqtt | Update MQTT config |
| POST | /api/firmware/upload | Upload firmware file |
| GET | /api/firmware/list | List firmware files |
| GET | /api/firmware/{name} | Download firmware |
| GET | /api/ota/queue | List OTA queue |
| POST | /api/ota/queue | Add to OTA queue |
| DELETE | /api/ota/queue/{id} | Remove from queue |
| GET | /health | Health check |

## Directory Structure

```
kamoa-ota-server/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── mqtt_client.py    # MQTT client
│   ├── storage.py        # JSON file storage
│   ├── api/              # API routers
│   ├── .env              # MQTT configuration
│   ├── data/             # Device/queue JSON files
│   └── firmware/         # Firmware files
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
├── data/                 # Local data (Docker volume)
├── firmware/             # Local firmware (Docker volume)
├── docker-compose.yml
└── Dockerfile.backend
```

## OTA Flow

1. User uploads firmware file via UI
2. User adds device to OTA queue with selected firmware
3. Backend monitors for device sending "ready" on `{device_id}/device/status`
4. When device is ready and in queue, backend sends OTA command via MQTT
5. Queue status updates based on device responses

## Configuration

MQTT settings can be configured:
1. Via `backend/.env` file (loaded on startup)
2. Via UI Settings panel (saved to `data/config.json`)

The UI settings take precedence and persist across restarts.