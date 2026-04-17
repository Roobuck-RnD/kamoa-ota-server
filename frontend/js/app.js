/**
 * Main application logic.
 */

// Navigation functions
function showDashboard() {
    updateNavigation('nav-dashboard');
    showSection('dashboard-section');
    refreshDevices();
}

function showSettings() {
    updateNavigation('nav-settings');
    showSection('settings-section');
    loadMqttConfig();
}

function showFirmware() {
    updateNavigation('nav-firmware');
    showSection('firmware-section');
    refreshFirmwareList();
}

function showOtaQueue() {
    updateNavigation('nav-ota');
    showSection('ota-section');
    refreshOtaQueue();
    refreshOtaDevices();
}

// Register WebSocket message handlers
function registerWebSocketHandlers() {
    // Register handler for OTA progress updates
    if (typeof onMessage === 'function') {
        onMessage('ota_progress', function(data) {
            if (typeof updateOtaProgress === 'function') {
                updateOtaProgress(data);
            }
        });
    }
}

/**
 * Update navigation button states.
 */
function updateNavigation(activeId) {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(activeId).classList.add('active');
}

/**
 * Show a specific section.
 */
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
}

/**
 * Initialize application.
 */
async function initApp() {
    console.log('Initializing OTA Server UI...');
    
    // Initialize toast system
    if (typeof ToastManager === 'object' && ToastManager.init) {
        ToastManager.init();
    }
    
    // Initialize WebSocket connection
    if (typeof initWebSocket === 'function') {
        initWebSocket();
    }
    
    // Register WebSocket message handlers
    registerWebSocketHandlers();
    
    // Initial data load
    await refreshDevices();
    await refreshFirmwareList();
    await refreshOtaQueue();
    await updateHealthStatus();
    
    // Set up polling for updates (reduced frequency since we have WebSocket)
    setInterval(() => {
        refreshDevices();
        updateHealthStatus();
    }, 10000); // Refresh every 10 seconds (WebSocket handles real-time updates)
    
    console.log('OTA Server UI initialized');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);
