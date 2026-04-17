/**
 * WebSocket client for real-time OTA progress updates.
 */

// WebSocket message types
const WsMessageType = {
    CONNECTED: 'connected',
    DEVICE_UPDATE: 'device_update',
    OTA_PROGRESS: 'ota_progress',
    QUEUE_UPDATE: 'queue_update',
    MQTT_STATUS: 'mqtt_status'
};

// WebSocket client state
let websocket = null;
let reconnectAttempts = 0;
let maxReconnectAttempts = 10;
let reconnectDelay = 1000; // Start with 1 second
let reconnectTimer = null;
let isConnecting = false;

// Callback functions for message handling
let messageHandlers = {
    [WsMessageType.CONNECTED]: [],
    [WsMessageType.DEVICE_UPDATE]: [],
    [WsMessageType.OTA_PROGRESS]: [],
    [WsMessageType.QUEUE_UPDATE]: [],
    [WsMessageType.MQTT_STATUS]: []
};

/**
 * Initialize WebSocket connection.
 */
function initWebSocket() {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected');
        return;
    }
    
    connect();
}

/**
 * Connect to WebSocket server.
 */
function connect() {
    if (isConnecting) {
        return;
    }
    
    isConnecting = true;
    
    // Determine WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    
    try {
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function(event) {
            console.log('WebSocket connected');
            isConnecting = false;
            reconnectAttempts = 0;
            reconnectDelay = 1000;
            updateWebSocketStatus(true);
            notifyHandlers(WsMessageType.CONNECTED, { connected: true });
        };
        
        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data.type);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        websocket.onclose = function(event) {
            console.log('WebSocket disconnected:', event.code, event.reason);
            isConnecting = false;
            updateWebSocketStatus(false);
            notifyHandlers(WsMessageType.CONNECTED, { connected: false });
            
            // Attempt to reconnect
            scheduleReconnect();
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            isConnecting = false;
        };
        
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        isConnecting = false;
        scheduleReconnect();
    }
}

/**
 * Schedule a reconnection attempt.
 */
function scheduleReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) {
        console.log('Max reconnection attempts reached');
        return;
    }
    
    reconnectAttempts++;
    console.log(`Scheduling reconnection attempt ${reconnectAttempts}/${maxReconnectAttempts} in ${reconnectDelay}ms`);
    
    reconnectTimer = setTimeout(() => {
        console.log('Attempting to reconnect...');
        connect();
        // Exponential backoff
        reconnectDelay = Math.min(reconnectDelay * 2, 30000); // Max 30 seconds
    }, reconnectDelay);
}

/**
 * Cancel pending reconnection.
 */
function cancelReconnect() {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
}

/**
 * Handle incoming WebSocket messages.
 * @param {Object} data - The parsed message data
 */
function handleWebSocketMessage(data) {
    const type = data.type;
    
    // Notify registered handlers
    notifyHandlers(type, data);
    
    // Handle specific message types
    switch (type) {
        case WsMessageType.OTA_PROGRESS:
            handleOtaProgress(data);
            break;
        case WsMessageType.DEVICE_UPDATE:
            handleDeviceUpdate(data);
            break;
        case WsMessageType.QUEUE_UPDATE:
            handleQueueUpdate(data);
            break;
        case WsMessageType.MQTT_STATUS:
            handleMqttStatus(data);
            break;
    }
}

/**
 * Handle OTA progress update.
 * @param {Object} data - The progress data
 */
function handleOtaProgress(data) {
    console.log('OTA Progress:', data);
    // Update the progress bar in the OTA queue
    updateOtaProgressInUI(data);
}

/**
 * Handle device update.
 * @param {Object} data - The device data
 */
function handleDeviceUpdate(data) {
    console.log('Device update:', data);
    // Could trigger a refresh of the device list
}

/**
 * Handle queue update.
 * @param {Object} data - The queue data
 */
function handleQueueUpdate(data) {
    console.log('Queue update:', data);
    // Refresh the OTA queue
    if (typeof refreshOtaQueue === 'function') {
        refreshOtaQueue();
    }
}

/**
 * Handle MQTT status change.
 * @param {Object} data - The status data
 */
function handleMqttStatus(data) {
    console.log('MQTT status:', data);
    // Update MQTT status indicator
}

/**
 * Update OTA progress in the UI.
 * @param {Object} data - The progress data
 */
function updateOtaProgressInUI(data) {
    // Find the queue item row
    const row = document.querySelector(`[data-queue-id="${data.queue_id}"]`);
    if (!row) {
        console.log('Queue row not found for ID:', data.queue_id);
        return;
    }
    
    // Find or create progress cell
    let progressCell = row.querySelector('.ota-progress-cell');
    if (!progressCell) {
        // Add progress column if it doesn't exist
        progressCell = document.createElement('td');
        progressCell.className = 'ota-progress-cell';
        row.insertBefore(progressCell, row.lastElementChild);
    }
    
    // Render progress bar
    progressCell.innerHTML = renderProgressBar(data);
}

/**
 * Render progress bar HTML.
 * @param {Object} data - The progress data
 * @returns {string} HTML string
 */
function renderProgressBar(data) {
    const percentage = Math.round(data.percentage);
    const bytes = formatBytes(data.progress);
    const totalBytes = formatBytes(data.firmware_size);
    
    let statusClass = 'progress';
    if (data.finished === 1) {
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
 * Format bytes to human readable format.
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted string
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Update WebSocket status indicator.
 * @param {boolean} connected - Connection status
 */
function updateWebSocketStatus(connected) {
    const wsStatus = document.getElementById('websocket-status');
    if (wsStatus) {
        wsStatus.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
        wsStatus.title = connected ? 'WebSocket Connected' : 'WebSocket Disconnected';
    }
}

/**
 * Send a message through WebSocket.
 * @param {Object} data - The message data
 */
function sendWebSocketMessage(data) {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify(data));
    }
}

/**
 * Register a callback handler for a message type.
 * @param {string} type - The message type
 * @param {Function} callback - The callback function
 */
function onMessage(type, callback) {
    if (messageHandlers[type]) {
        messageHandlers[type].push(callback);
    }
}

/**
 * Notify all handlers for a message type.
 * @param {string} type - The message type
 * @param {Object} data - The message data
 */
function notifyHandlers(type, data) {
    if (messageHandlers[type]) {
        messageHandlers[type].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('Error in WebSocket message handler:', error);
            }
        });
    }
}

/**
 * Close WebSocket connection.
 */
function closeWebSocket() {
    cancelReconnect();
    if (websocket) {
        websocket.close();
        websocket = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Defer initial connection
    setTimeout(initWebSocket, 500);
});