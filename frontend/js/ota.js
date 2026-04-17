/**
 * OTA update logic and queue management.
 * 
 * Handles firmware upload, OTA queue management, and device update operations.
 */

let firmwareList = [];
let otaQueue = [];
let devicesList = [];
let otaProgressData = {}; // Store progress data by queue_id

/**
 * Upload firmware file.
 */
async function uploadFirmware() {
    const fileInput = document.getElementById('firmware-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select a firmware file first.', ToastType.ERROR);
        return;
    }
    
    try {
        const result = await uploadFirmwareFile(file);
        showToast(`Firmware uploaded: ${result.filename}`, ToastType.SUCCESS);
        
        // Clear file input
        fileInput.value = '';
        
        // Refresh firmware list
        await refreshFirmwareList();
    } catch (error) {
        showToast('Failed to upload firmware: ' + error.message, ToastType.ERROR);
    }
}

/**
 * Delete a firmware file.
 * @param {string} filename - The firmware filename to delete.
 */
async function deleteFirmwareFile(filename) {
    if (!confirm(`Delete firmware file "${filename}"? This cannot be undone.`)) {
        return;
    }
    
    try {
        await deleteFirmware(filename);
        showToast(`Firmware "${filename}" deleted successfully.`, ToastType.SUCCESS);
        
        // Refresh firmware list
        await refreshFirmwareList();
        
        // Also refresh OTA devices table if on OTA page
        if (document.getElementById('ota-devices-body')) {
            await refreshOtaDevices();
        }
    } catch (error) {
        showToast('Failed to delete firmware: ' + error.message, ToastType.ERROR);
    }
}

/**
 * Refresh firmware list.
 */
async function refreshFirmwareList() {
    try {
        firmwareList = await fetchFirmwareList();
        renderFirmwareTable(firmwareList);
    } catch (error) {
        showToast('Failed to fetch firmware list: ' + error.message, ToastType.ERROR);
        renderFirmwareTable([]);
    }
}

/**
 * Render firmware table with delete button.
 * @param {Array} firmware - List of firmware metadata objects.
 */
function renderFirmwareTable(firmware) {
    const tbody = document.getElementById('firmware-body');
    
    if (!firmware || firmware.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No firmware files uploaded.</td></tr>';
        return;
    }
    
    tbody.innerHTML = firmware.map(f => `
        <tr>
            <td><code>${escapeHtml(f.filename)}</code></td>
            <td>${formatFileSize(f.size)}</td>
            <td><code>${escapeHtml(f.md5_hash)}</code></td>
            <td>${formatDateTime(f.uploaded_at)}</td>
            <td>
                <a href="/api/firmware/${escapeHtml(f.filename)}" download class="btn btn-success btn-small">
                    Download
                </a>
                <button class="btn btn-danger btn-small" onclick="deleteFirmwareFile('${escapeHtml(f.filename)}')">
                    Delete
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Refresh devices list for OTA page.
 */
async function refreshOtaDevices() {
    try {
        devicesList = await fetchDevices();
        renderOtaDevicesTable(devicesList);
    } catch (error) {
        // showToast('Failed to fetch devices: ' + error.message, ToastType.ERROR);
        renderOtaDevicesTable([]);
    }
}

/**
 * Render devices table on OTA page with queue controls.
 * @param {Array} devices - List of device objects.
 */
function renderOtaDevicesTable(devices) {
    const tbody = document.getElementById('ota-devices-body');
    
    if (!devices || devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No devices found. Devices will appear here when they connect via MQTT.</td></tr>';
        return;
    }
    
    // Build firmware options
    const firmwareOptions = firmwareList.length > 0 
        ? firmwareList.map(f => `<option value="${escapeHtml(f.filename)}">${escapeHtml(f.filename)}</option>`).join('')
        : '<option value="">No firmware available</option>';
    
    tbody.innerHTML = devices.map(device => {
        // Check if device is already in queue
        const queuedItem = otaQueue.find(item => item.device_id === device.device_id);
        const isInQueue = queuedItem !== undefined;
        
        return `
            <tr>
                <td><code>${escapeHtml(device.device_id)}</code></td>
                <td>${device.ip_address || '<span class="no-data">-</span>'}</td>
                <td>${device.firmware_version || '<span class="no-data">-</span>'}</td>
                <td>${device.is_online ? '<span class="status-badge online">Online</span>' : '<span class="status-badge offline">Offline</span>'}</td>
                <td>
                    <select id="firmware-select-${escapeHtml(device.device_id)}" class="firmware-select">
                        <option value="">Select Firmware...</option>
                        ${firmwareOptions}
                    </select>
                </td>
                <td>
                    ${isInQueue 
                        ? `<button class="btn btn-warning btn-small" onclick="toggleDeviceInQueue('${escapeHtml(device.device_id)}', 'remove')">Remove from Queue</button>`
                        : `<button class="btn btn-primary btn-small" onclick="toggleDeviceInQueue('${escapeHtml(device.device_id)}', 'add')">Add to Queue</button>`
                    }
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Toggle device in/out of OTA queue.
 * @param {string} deviceId - The device ID to add/remove.
 * @param {string} action - 'add' or 'remove'.
 */
async function toggleDeviceInQueue(deviceId, action) {
    if (action === 'add') {
        // Get selected firmware for this device
        const firmwareSelect = document.getElementById(`firmware-select-${deviceId}`);
        const firmwareFilename = firmwareSelect.value;
        
        if (!firmwareFilename) {
            showToast('Please select a firmware file for this device.', ToastType.ERROR);
            return;
        }
        
        try {
            await addToOtaQueue(deviceId, firmwareFilename);
            showToast(`Device ${deviceId} added to OTA queue.`, ToastType.SUCCESS);
        } catch (error) {
            showToast('Failed to add to queue: ' + error.message, ToastType.ERROR);
        }
    } else {
        // Remove from queue - find the queue item for this device
        const queuedItem = otaQueue.find(item => item.device_id === deviceId);
        if (queuedItem) {
            try {
                await removeFromOtaQueue(queuedItem.id);
                showToast(`Device ${deviceId} removed from queue.`, ToastType.SUCCESS);
            } catch (error) {
                showToast('Failed to remove from queue: ' + error.message, ToastType.ERROR);
            }
        }
    }
    
    // Refresh both tables
    await refreshOtaQueue();
    await refreshOtaDevices();
}

/**
 * Refresh OTA queue.
 */
async function refreshOtaQueue() {
    try {
        otaQueue = await fetchOtaQueue();
        renderOtaQueueTable(otaQueue);
        
        // Also refresh devices table to update queue status buttons
        if (devicesList.length > 0) {
            renderOtaDevicesTable(devicesList);
        }
    } catch (error) {
        showToast('Failed to fetch OTA queue: ' + error.message, ToastType.ERROR);
        renderOtaQueueTable([]);
    }
}

/**
 * Render OTA queue table.
 * @param {Array} queue - List of queue items.
 */
function renderOtaQueueTable(queue) {
    const tbody = document.getElementById('ota-queue-body');
    
    if (!queue || queue.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No items in queue.</td></tr>';
        return;
    }
    
    tbody.innerHTML = queue.map(item => {
        const progressData = otaProgressData[item.id];
        const progressHtml = renderProgressCell(item, progressData);
        const actionHtml = item.status === 'pending' 
            ? `<button class="btn btn-danger btn-small" onclick="removeFromQueue(${item.id})">Remove</button>` 
            : '<span class="no-data">-</span>';
        
        return `
            <tr data-queue-id="${item.id}">
                <td>${item.id}</td>
                <td><code>${escapeHtml(item.device_id)}</code></td>
                <td><code>${escapeHtml(item.firmware_filename)}</code></td>
                <td>${renderStatusBadge(item.status)}</td>
                <td class="ota-progress-cell">${progressHtml}</td>
                <td>${formatDateTime(item.created_at)}</td>
                <td>${actionHtml}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Render progress cell for OTA queue item.
 * @param {Object} item - The queue item.
 * @param {Object} progressData - The progress data (if any).
 * @returns {string} HTML string.
 */
function renderProgressCell(item, progressData) {
    if (!progressData) {
        return '<span class="no-progress">-</span>';
    }
    
    const percentage = Math.round(progressData.percentage);
    const bytes = formatFileSize(progressData.progress);
    const totalBytes = formatFileSize(progressData.firmware_size);
    
    let statusClass = 'progress';
    if (progressData.finished === 1) {
        statusClass = 'completed';
    }
    
    return `
        <div class="progress-bar-container">
            <div class="progress-bar-wrapper">
                <div class="progress-bar-fill ${statusClass}" style="width: ${percentage}%"></div>
            </div>
            <div class="progress-bar-text">
                <span class="progress-percentage">${percentage}%</span>
                <span class="progress-details">${bytes} / ${totalBytes}</span>
            </div>
        </div>
    `;
}

/**
 * Update OTA progress data from WebSocket message.
 * @param {Object} data - The progress data from WebSocket.
 */
function updateOtaProgress(data) {
    otaProgressData[data.queue_id] = data;
    
    // Update the progress bar in the existing table row
    const row = document.querySelector(`[data-queue-id="${data.queue_id}"]`);
    if (row) {
        const progressCell = row.querySelector('.ota-progress-cell');
        if (progressCell) {
            // Find the queue item to pass to renderProgressCell
            const queueItem = otaQueue.find(item => item.id === data.queue_id);
            if (queueItem) {
                progressCell.innerHTML = renderProgressCell(queueItem, data);
            }
        }
    }
    
    // Show toast notification for significant events
    if (data.reason === 'begin') {
        showToast(`OTA update started for device ${data.device_id}`, ToastType.INFO);
    } else if (data.reason === 'finished') {
        showToast(`OTA update completed for device ${data.device_id}`, ToastType.SUCCESS);
        // Refresh queue to update status
        setTimeout(refreshOtaQueue, 1000);
    }
}

/**
 * Remove item from queue by ID.
 * @param {number} queueId - The queue item ID to remove.
 */
async function removeFromQueue(queueId) {
    if (!confirm('Remove this item from the OTA queue?')) {
        return;
    }
    
    try {
        await apiRequest(`/ota/queue/${queueId}`, {
            method: 'DELETE',
        });
        
        showToast('Removed from queue.', ToastType.SUCCESS);
        await refreshOtaQueue();
    } catch (error) {
        showToast('Failed to remove from queue: ' + error.message, ToastType.ERROR);
    }
}

/**
 * Format file size to human-readable string.
 * @param {number} bytes - File size in bytes.
 * @returns {string} Formatted file size.
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format datetime to human-readable string.
 * @param {string} isoString - ISO format datetime string.
 * @returns {string} Formatted datetime.
 */
function formatDateTime(isoString) {
    if (!isoString) return '<span class="no-data">-</span>';
    try {
        const date = new Date(isoString);
        return date.toLocaleString();
    } catch (e) {
        return isoString;
    }
}

/**
 * Render status badge with appropriate styling.
 * @param {string} status - The status string.
 * @returns {string} HTML badge.
 */
function renderStatusBadge(status) {
    const statusClass = status ? status.toLowerCase() : 'unknown';
    return `<span class="status-badge ${statusClass}">${escapeHtml(status || 'Unknown')}</span>`;
}

/**
 * Escape HTML special characters.
 * @param {string} text - Text to escape.
 * @returns {string} Escaped text.
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}