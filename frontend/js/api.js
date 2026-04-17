/**
 * API client functions for communicating with the backend.
 */

const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling.
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

/**
 * Devices API
 */
async function fetchDevices() {
    return apiRequest('/devices/');
}

async function fetchDevice(deviceId) {
    return apiRequest(`/devices/${deviceId}`);
}

/**
 * Config API
 */
async function fetchMqttConfig() {
    return apiRequest('/config/mqtt/');
}

async function updateMqttConfig(config) {
    return apiRequest('/config/mqtt/', {
        method: 'POST',
        body: JSON.stringify(config),
    });
}

/**
 * Firmware API
 */
async function fetchFirmwareList() {
    return apiRequest('/firmware/list');
}

async function uploadFirmwareFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/firmware/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Firmware upload error:', error);
        throw error;
    }
}

/**
 * OTA Queue API
 */
async function fetchOtaQueue() {
    return apiRequest('/ota/queue/');
}

async function addToOtaQueue(deviceId, firmwareFilename) {
    return apiRequest('/ota/queue/', {
        method: 'POST',
        body: JSON.stringify({
            device_id: deviceId,
            firmware_filename: firmwareFilename,
        }),
    });
}

async function removeFromOtaQueue(queueId) {
    return apiRequest(`/ota/queue/${queueId}`, {
        method: 'DELETE',
    });
}

async function updateOtaQueueStatus(queueId, status, errorMessage = null) {
    return apiRequest(`/ota/queue/${queueId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, error_message: errorMessage }),
    });
}

/**
 * Health Check API
 */
async function checkHealth() {
    return apiRequest('/health');
}