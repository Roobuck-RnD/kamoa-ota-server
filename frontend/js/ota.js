/**
 * OTA update logic and queue management.
 */

let firmwareList = [];
let otaQueue = [];

/**
 * Upload firmware file.
 */
async function uploadFirmware() {
    const fileInput = document.getElementById('firmware-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Please select a firmware file first.');
        return;
    }
    
    try {
        const result = await uploadFirmwareFile(file);
        showSuccess(`Firmware uploaded: ${result.filename}`);
        
        // Clear file input
        fileInput.value = '';
        
        // Refresh firmware list
        await refreshFirmwareList();
    } catch (error) {
        showError('Failed to upload firmware: ' + error.message);
    }
}

/**
 * Refresh firmware list.
 */
async function refreshFirmwareList() {
    try {
        firmwareList = await fetchFirmwareList();
        renderFirmwareTable(firmwareList);
        updateFirmwareSelect(firmwareList);
    } catch (error) {
        showError('Failed to fetch firmware list: ' + error.message);
        renderFirmwareTable([]);
    }
}

/**
 * Render firmware table.
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
                <a href="/firmware/${escapeHtml(f.filename)}" download class="btn btn-success">
                    Download
                </a>
            </td>
        </tr>
    `).join('');
}

/**
 * Update firmware select dropdown.
 */
function updateFirmwareSelect(firmware) {
    const select = document.getElementById('ota-firmware-select');
    const currentValue = select.value;
    
    select.innerHTML = '<option value="">Select Firmware...</option>';
    
    firmware.forEach(f => {
        const option = document.createElement('option');
        option.value = f.filename;
        option.textContent = f.filename;
        select.appendChild(option);
    });
    
    // Restore selection if still valid
    if (firmware.some(f => f.filename === currentValue)) {
        select.value = currentValue;
    }
}

/**
 * Add device to OTA queue.
 */
async function addToOtaQueue() {
    const deviceId = document.getElementById('ota-device-select').value;
    const firmwareFilename = document.getElementById('ota-firmware-select').value;
    
    if (!deviceId) {
        showError('Please select a device.');
        return;
    }
    
    if (!firmwareFilename) {
        showError('Please select a firmware file.');
        return;
    }
    
    try {
        await apiRequest('/ota/queue/', {
            method: 'POST',
            body: JSON.stringify({
                device_id: deviceId,
                firmware_filename: firmwareFilename,
            }),
        });
        
        showSuccess('Added to OTA queue!');
        await refreshOtaQueue();
    } catch (error) {
        showError('Failed to add to queue: ' + error.message);
    }
}

/**
 * Refresh OTA queue.
 */
async function refreshOtaQueue() {
    try {
        otaQueue = await fetchOtaQueue();
        renderOtaQueue(otaQueue);
    } catch (error) {
        showError('Failed to fetch OTA queue: ' + error.message);
        renderOtaQueue([]);
    }
}

/**
 * Render OTA queue table.
 */
function renderOtaQueue(queue) {
    const tbody = document.getElementById('ota-body');
    
    if (!queue || queue.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">OTA queue is empty.</td></tr>';
        return;
    }
    
    tbody.innerHTML = queue.map(item => `
        <tr>
            <td>${item.id}</td>
            <td><code>${escapeHtml(item.device_id)}</code></td>
            <td><code>${escapeHtml(item.firmware_filename)}</code></td>
            <td>${renderStatusBadge(item.status)}</td>
            <td>${formatDateTime(item.created_at)}</td>
            <td>
                ${item.status === 'pending' ? 
                    `<button class="btn btn-danger" onclick="removeFromQueue(${item.id})">Remove</button>` : 
                    ''}
            </td>
        </tr>
    `).join('');
}

/**
 * Remove item from queue.
 */
async function removeFromQueue(queueId) {
    if (!confirm('Remove this item from the OTA queue?')) {
        return;
    }
    
    try {
        await apiRequest(`/ota/queue/${queueId}`, {
            method: 'DELETE',
        });
        
        showSuccess('Removed from queue.');
        await refreshOtaQueue();
    } catch (error) {
        showError('Failed to remove from queue: ' + error.message);
    }
}

/**
 * Format file size.
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}