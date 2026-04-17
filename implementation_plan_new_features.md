# Implementation Plan - OTA Server Enhancements

## Overview
This document outlines the implementation of 6 new features and fixes for the IoT OTA Update Server, including filtering functionality, UI reorganization, and improved OTA queue management logic.

## Requirements

### 1. Dynamic Server URL for OTA Commands
Set the firmware server URL dynamically based on the frontend's window location (hostname, port, protocol) instead of hardcoded localhost. Prevent sending OTA commands when the URL is localhost.

### 2. Filtering by Partial Device ID or Firmware Version
Add search/filter input fields on both the Dashboard and OTA Queue pages. Filtering should trigger when the user presses Enter, filtering devices by partial match on device_id or firmware_version.

### 3. Single Firmware Dropdown on OTA Queue Page
Replace per-device firmware selectors with a single global firmware dropdown at the top of the OTA Queue page. When adding a device to the queue, use the globally selected firmware.

### 4. Reorder OTA Queue Page Tables
Move the "Update Queue" table above the "Available Devices" table on the OTA Queue page for better visibility of active updates.

### 5. Conditional OTA Command Sending
Modify `send_ota_command()` to only send when the queue item status is "pending". Currently, it sends whenever a device reports "ready" regardless of queue status.

### 6. OTA Queue Status Management Based on finished Flag
- Remove device from OTA queue ONLY when `update/otaStatus` returns `finished: 1` (success)
- When `update/otaStatus` returns `finished: -1` (failure), change queue status from "in_progress" to "pending" to allow retry

---

[Types]
No new types required. Existing types are sufficient:
- `OtaQueueItem` in `backend/storage.py` - already has `status` field
- `OtaProgress` in `backend/storage.py` - already has `finished` field

[Files]
New files: None

Modified files:
- `backend/mqtt_client.py` - Modify `send_ota_command()` to use dynamic URL and check pending status; Modify `_handle_ota_progress()` to handle finished: -1
- `backend/main.py` - Add environment variable for SERVER_URL with dynamic detection
- `frontend/index.html` - Add filter input fields; Reorder OTA queue tables; Replace per-device dropdowns with single global dropdown
- `frontend/js/ota.js` - Add filtering logic; Update to use global firmware selector; Update table ordering
- `frontend/js/dashboard.js` - Add filtering logic for devices table
- `frontend/css/style.css` - Add styles for filter input fields

[Functions]

**New Functions:**
- `frontend/js/ota.js`: `filterOtaDevices(query)` - Filter devices list by device_id or firmware_version
- `frontend/js/ota.js`: `filterOtaQueue(query)` - Filter queue items by device_id or firmware_filename
- `frontend/js/dashboard.js`: `filterDevices(query)` - Filter devices list by device_id or firmware_version
- `backend/mqtt_client.py`: `get_server_url()` - Get dynamic server URL from environment or window location

**Modified Functions:**
- `backend/mqtt_client.py::send_ota_command()` - Add pending status check before sending; Use dynamic server URL
- `backend/mqtt_client.py::_handle_ota_progress()` - Handle finished: -1 case to reset status to pending
- `frontend/js/ota.js::toggleDeviceInQueue()` - Use global firmware selector instead of per-device
- `frontend/js/ota.js::renderOtaDevicesTable()` - Remove per-device firmware dropdown
- `frontend/js/ota.js::renderOtaQueueTable()` - No changes needed, just reorder in HTML

[Classes]
No new classes required. No class modifications needed.

[Dependencies]
No new dependencies required.

[Testing]
1. Test filtering on Dashboard page:
   - Enter partial device ID, verify filtered results
   - Enter partial firmware version, verify filtered results
   - Clear filter, verify all devices shown

2. Test filtering on OTA Queue page:
   - Same as above for devices table
   - Test filtering on queue table

3. Test single firmware dropdown:
   - Select firmware, add device to queue, verify correct firmware is assigned
   - Change firmware selection, add another device, verify new firmware is assigned

4. Test OTA command sending:
   - Add device to queue (status: pending)
   - Send "ready" from device, verify command is sent
   - Manually change status to in_progress, send "ready" again, verify command is NOT sent

5. Test OTA completion handling:
   - Simulate finished: 1, verify device removed from queue
   - Simulate finished: -1, verify status changed to pending

6. Test dynamic server URL:
   - Access from localhost, verify URL uses localhost
   - Access from different host, verify URL uses that host

[Implementation Order]

1. **Backend - Dynamic Server URL**
   - Modify `backend/mqtt_client.py::send_ota_command()` to read SERVER_URL from environment
   - Add fallback to construct URL from request context if possible

2. **Backend - OTA Queue Status Logic**
   - Modify `backend/mqtt_client.py::_check_and_trigger_ota()` to only trigger when status is "pending"
   - Modify `backend/mqtt_client.py::_handle_ota_progress()` to handle finished: -1 case

3. **Frontend - HTML Structure Changes**
   - Add filter input field to Dashboard section
   - Add filter input field to OTA Queue section
   - Add global firmware dropdown at top of OTA Queue section
   - Reorder tables (Update Queue above Available Devices)
   - Remove per-device firmware dropdowns

4. **Frontend - JavaScript Logic**
   - Add `filterDevices()` function in `dashboard.js`
   - Add `filterOtaDevices()` and `filterOtaQueue()` functions in `ota.js`
   - Update `toggleDeviceInQueue()` to use global firmware selector
   - Update `renderOtaDevicesTable()` to remove per-device dropdown

5. **Frontend - CSS Styling**
   - Add styles for filter input fields
   - Add styles for global firmware selector

6. **Testing and Verification**
   - Test all features end-to-end
   - Verify no regressions in existing functionality

---

## Detailed Implementation Notes

### Dynamic Server URL
The `send_ota_command()` function currently uses:
```python
server_url = os.environ.get("SERVER_URL", "http://localhost:8000")
```

This should be configurable via environment variable. The frontend cannot directly influence this, but we can:
1. Set SERVER_URL in docker-compose.yml or .env
2. Add a setting in the UI to configure the external server URL
3. Use the request's host header if available (requires passing request context)

For now, option 1 is the simplest - document that SERVER_URL should be set appropriately.

### Filtering Implementation
Filter should be case-insensitive partial match:
```javascript
function filterDevices(query) {
    if (!query) {
        renderDeviceTable(devicesData);
        return;
    }
    const filtered = devicesData.filter(device => 
        device.device_id.toLowerCase().includes(query.toLowerCase()) ||
        (device.firmware_version && device.firmware_version.toLowerCase().includes(query.toLowerCase()))
    );
    renderDeviceTable(filtered);
}
```

### Global Firmware Selector
Replace the per-device select with a single select at the top:
```html
<h3>Update Queue</h3>
<div class="controls">
    <label for="global-firmware-select">Select Firmware:</label>
    <select id="global-firmware-select" class="firmware-select">
        <option value="">Select Firmware...</option>
        <!-- options populated from firmwareList -->
    </select>
</div>
<div class="table-container">
    <!-- queue table -->
</div>
```

### OTA Progress Handling
Current logic in `_handle_ota_progress()`:
```python
if finished == 1:
    update_queue_status(queue_item.id, "completed")
    clear_ota_progress(device_id)
```

Add handling for finished == -1:
```python
if finished == 1:
    update_queue_status(queue_item.id, "completed")
    clear_ota_progress(device_id)
    # Remove from queue
    remove_from_queue(queue_item.id)
elif finished == -1:
    # Failed - reset to pending for retry
    update_queue_status(queue_item.id, "pending", reason)
    clear_ota_progress(device_id)
```

---

## Navigation Commands

```bash
# Read Types section
sed -n '/\[Types\]/,/\[Files\]/p' implementation_plan_new_features.md | head -n -1

# Read Files section
sed -n '/\[Files\]/,/\[Functions\]/p' implementation_plan_new_features.md | head -n -1

# Read Functions section
sed -n '/\[Functions\]/,/\[Classes\]/p' implementation_plan_new_features.md | head -n -1

# Read Implementation Order section
sed -n '/\[Implementation Order\]/,$p' implementation_plan_new_features.md