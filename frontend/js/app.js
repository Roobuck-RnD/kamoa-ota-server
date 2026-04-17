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
    
    // Initial data load
    await refreshDevices();
    await refreshFirmwareList();
    await refreshOtaQueue();
    await updateHealthStatus();
    
    // Set up polling for updates
    setInterval(() => {
        refreshDevices();
        refreshOtaQueue();
        updateHealthStatus();
    }, 5000); // Refresh every 5 seconds
    
    console.log('OTA Server UI initialized');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);