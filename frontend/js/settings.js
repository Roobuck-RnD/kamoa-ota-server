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
        showError('Failed to load MQTT config: ' + error.message);
    }
}

/**
 * Save MQTT configuration.
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
        await updateMqttConfig(config);
        showSuccess('MQTT configuration saved successfully!');
        
        // Refresh health status after config change
        updateHealthStatus();
    } catch (error) {
        showError('Failed to save config: ' + error.message);
    }
}

/**
 * Show success message.
 */
function showSuccess(message) {
    alert(message);
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