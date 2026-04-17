# IoT OTA Update Server

A simple Over-The-Air (OTA) update system for IoT devices.

---

## Setup

### Step 1: Configure MQTT

Copy the example configuration file:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your settings:

```bash
nano backend/.env
```

```
SERVER_PORT=18000          # Port the server runs on
MQTT_URL=your-mqtt-broker  # MQTT broker address
MQTT_PORT=1883             # MQTT broker port
MQTT_USERNAME=your-username
MQTT_PASSWORD=your-password
```

### Step 2: Start with Docker

**Newer Docker (`docker compose`):**
```bash
docker compose up --build -d
```

**Older Docker (`docker-compose`):**
```bash
docker-compose up --build -d
```

### Step 3: Open in Browser

Go to the port you configured (default: 18000):

```
http://localhost:18000
```

---

## How to Use

### Configure MQTT (in the UI)

1. Go to **Settings** tab
2. Enter your MQTT broker address, port, username, password
3. Click **Save** — the system will reconnect automatically

### Configure Firmware Server URL

1. Go to **Settings** tab
2. Set the **Firmware Server URL** (the address devices use to download firmware)
3. Click **Save**

### Upload Firmware

1. Go to **Firmware** tab
2. Click **Choose File** and select your firmware file
3. Click **Upload**

### Update a Device

1. Go to **OTA Queue** tab
2. Select a firmware file for your device
3. Click **Add to Queue**
4. Wait for the device to be ready — update starts automatically
5. Watch the progress bar

---

## Status Indicators

| Indicator | Green | Red |
|-----------|-------|-----|
| MQTT | Connected | Disconnected |
| WebSocket | Live updates | Connection lost |

---

## Data Files

All data is stored in `data/`:
- `devices.json` — registered devices
- `queue.json` — update queue
- `config.json` — your settings

---

## License

Roobuck Inc. proprietary license