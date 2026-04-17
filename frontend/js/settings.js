/**
 * Settings panel logic for MQTT configuration.
 */

/**
 * Load and display current MQTT configuration.
 */
async function loadMqttConfig() {
    try {
        const config = await fetchMqttConfig();
        
        document.getElementById('broker-url').value = config.broker_url || '';
        document.getElementById('broker-port').value = config.broker_port || 1883;
        document.getElementById('mqtt-username').value = config.username || '';
        document.getElementById('mqtt-password').value = ''; // Don't show password
    } catch (error) {
        showToast('Failed to load MQTT config: ' + error.message, ToastType.ERROR);
    }
}

/**
 * Save MQTT configuration and trigger reconnection.
 */
async function saveMqttConfig(event) {
    event.preventDefault();
    
    const config = {
        broker_url: document.getElementById('broker-url').value,
        broker_port: parseInt(document.getElementById('broker-port').value),
        username: document.getElementById('mqtt-username').value || null,
        password: document.getElementById('mqtt-password').value || null,
    };
    
    try {
        // Save configuration
        await updateMqttConfig(config);
        showToast('MQTT configuration saved. Reconnecting...', ToastType.SUCCESS);
        
        // Trigger MQTT reconnection
        try {
            const reconnectResult = await reconnectMqtt();
            if (reconnectResult.connected) {
                showToast('MQTT reconnection successful!', ToastType.SUCCESS);
            } else {
                showToast('MQTT reconnection failed. Check broker settings.', ToastType.WARNING);
            }
        } catch (reconnectError) {
            console.error('Reconnection error:', reconnectError);
            showToast('MQTT reconnection failed: ' + reconnectError.message, ToastType.WARNING);
        }
        
        // Refresh health status after config change
        updateHealthStatus();
    } catch (error) {
        showToast('Failed to save config: ' + error.message, ToastType.ERROR);
    }
}

/**
 * Show success message.
 */
function showSuccess(message) {
    showToast(message, ToastType.SUCCESS);
}

/**
 * Show error message.
 */
function showError(message) {
    showToast(message, ToastType.ERROR);
}

/**
 * Update health status indicator.
 */
async function updateHealthStatus() {
    try {
        const health = await checkHealth();
        const statusDot = document.getElementById('mqtt-status');
        const statusText = document.getElementById('mqtt-status-text');
        
        if (health.mqtt_connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Disconnected';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        document.getElementById('mqtt-status').className = 'status-dot disconnected';
        document.getElementById('mqtt-status-text').textContent = 'Error';
    }
}

// ==================== Firmware Server Config ====================

/**
 * Load and display current firmware server configuration.
 */
async function loadFirmwareServerConfig() {
    try {
        const config = await fetchFirmwareServerConfig();
        
        document.getElementById('firmware-server-host').value = config.host || '';
        document.getElementById('firmware-server-port').value = config.port || 18000;
        document.getElementById('firmware-server-protocol').value = config.protocol || 'http';
    } catch (error) {
        console.error('Failed to load firmware server config:', error);
    }
}

/**
 * Save firmware server configuration.
 */
async function saveFirmwareServerConfig(event) {
    event.preventDefault();
    
    const host = document.getElementById('firmware-server-host').value.trim();
    const port = parseInt(document.getElementById('firmware-server-port').value);
    const protocol = document.getElementById('firmware-server-protocol').value;
    
    // Validate host is not localhost
    const hostLower = host.toLowerCase();
    if (hostLower === 'localhost' || hostLower === '127.0.0.1' || hostLower === '::1') {
        showToast('Firmware server host cannot be localhost. Please use the actual server IP address.', ToastType.ERROR);
        return;
    }
    
    // Validate port
    if (isNaN(port) || port < 1 || port > 65535) {
        showToast('Invalid port number. Must be between 1 and 65535.', ToastType.ERROR);
        return;
    }
    
    const config = {
        host: host,
        port: port,
        protocol: protocol
    };
    
    try {
        await updateFirmwareServerConfig(config);
        showToast('Firmware server configuration saved successfully.', ToastType.SUCCESS);
    } catch (error) {
        showToast('Failed to save firmware server config: ' + error.message, ToastType.ERROR);
    }
}
