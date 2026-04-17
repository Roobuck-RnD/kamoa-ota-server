/**
 * Dashboard rendering and device management.
 */

let devicesData = [];

/**
 * Fetch and display device list.
 */
async function refreshDevices() {
    try {
        devicesData = await fetchDevices();
        renderDeviceTable(devicesData);
        updateDeviceSelect(devicesData);
    } catch (error) {
        showError('Failed to fetch devices: ' + error.message);
        renderDeviceTable([]);
    }
}

/**
 * Render device table.
 */
function renderDeviceTable(devices) {
    const tbody = document.getElementById('devices-body');
    
    if (!devices || devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No devices found. Devices will appear here when they connect via MQTT.</td></tr>';
        return;
    }
    
    tbody.innerHTML = devices.map(device => `
        <tr>
            <td><code>${escapeHtml(device.device_id)}</code></td>
            <td>${escapeHtml(device.firmware_version || 'N/A')}</td>
            <td>${renderStatusBadge(device.status)}</td>
            <td>${renderOnlineBadge(device.is_online)}</td>
            <td>${formatDateTime(device.last_seen)}</td>
            <td>
                <button class="btn btn-primary" onclick="quickAddToQueue('${device.device_id}')">
                    Add to OTA
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Render status badge.
 */
function renderStatusBadge(status) {
    if (!status) return '<span class="status-badge offline">Unknown</span>';
    
    const statusClass = status.toLowerCase();
    return `<span class="status-badge ${statusClass}">${escapeHtml(status)}</span>`;
}

/**
 * Render online badge.
 */
function renderOnlineBadge(isOnline) {
    if (isOnline) {
        return '<span class="status-badge online">Online</span>';
    }
    return '<span class="status-badge offline">Offline</span>';
}

/**
 * Update device select dropdown.
 */
function updateDeviceSelect(devices) {
    const select = document.getElementById('ota-device-select');
    const currentValue = select.value;
    
    select.innerHTML = '<option value="">Select Device...</option>';
    
    devices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.device_id;
        option.textContent = `${device.device_id} - ${device.firmware_version || 'N/A'}`;
        select.appendChild(option);
    });
    
    // Restore selection if still valid
    if (devices.some(d => d.device_id === currentValue)) {
        select.value = currentValue;
    }
}

/**
 * Format datetime string.
 */
function formatDateTime(isoString) {
    if (!isoString) return 'Never';
    
    try {
        const date = new Date(isoString);
        return date.toLocaleString();
    } catch (e) {
        return isoString;
    }
}

/**
 * Escape HTML to prevent XSS.
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show error message.
 */
function showError(message) {
    alert(message);
}

/**
 * Quick add to queue from device row.
 */
function quickAddToQueue(deviceId) {
    showOtaQueue();
    document.getElementById('ota-device-select').value = deviceId;
}