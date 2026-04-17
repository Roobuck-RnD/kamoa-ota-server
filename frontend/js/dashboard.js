/**
 * Dashboard rendering and device management.
 * 
 * Handles displaying connected IoT devices with their status information.
 */

let devicesData = [];

/**
 * Fetch and display device list.
 */
async function refreshDevices() {
    try {
        devicesData = await fetchDevices();
        renderDeviceTable(devicesData);
    } catch (error) {
        // showToast('Failed to fetch devices: ' + error.message, ToastType.ERROR);
        renderDeviceTable([]);
    }
}

/**
 * Render device table with all device information.
 * Displays: Device ID, IP Address, Firmware Version, Operating Mode, Status, Online, Last Seen
 * @param {Array} devices - List of device objects.
 */
function renderDeviceTable(devices) {
    const tbody = document.getElementById('devices-body');
    
    if (!devices || devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No devices found. Devices will appear here when they connect via MQTT.</td></tr>';
        return;
    }
    
    tbody.innerHTML = devices.map(device => `
        <tr>
            <td><code>${escapeHtml(device.device_id)}</code></td>
            <td>${device.ip_address ? escapeHtml(device.ip_address) : '<span class="no-data">-</span>'}</td>
            <td>${device.firmware_version ? escapeHtml(device.firmware_version) : '<span class="no-data">-</span>'}</td>
            <td>${device.operating_mode ? escapeHtml(device.operating_mode) : '<span class="no-data">-</span>'}</td>
            <td>${renderOnlineBadge(device.is_online)}</td>
            <td>${formatDateTime(device.last_seen)}</td>
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
 * Format datetime string to human-readable format.
 * @param {string} isoString - ISO format datetime string.
 * @returns {string} Formatted datetime or 'Never' if empty.
 */
function formatDateTime(isoString) {
    if (!isoString) return '<span class="no-data">Never</span>';
    
    try {
        const date = new Date(isoString);
        return date.toLocaleString();
    } catch (e) {
        return isoString;
    }
}

/**
 * Escape HTML to prevent XSS attacks.
 * @param {string} text - Text to escape.
 * @returns {string} Escaped text.
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
