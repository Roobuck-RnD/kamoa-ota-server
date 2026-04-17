/**
 * Toast notification system for elegant user feedback.
 */

// Toast notification types
const ToastType = {
    SUCCESS: 'success',
    ERROR: 'error',
    INFO: 'info',
    WARNING: 'warning'
};

// Toast configuration
const ToastConfig = {
    DEFAULT_DURATION: 4000,  // 4 seconds
    MIN_DURATION: 2000,
    MAX_DURATION: 10000
};

/**
 * Toast manager module.
 */
const ToastManager = (function() {
    let toastContainer = null;
    
    /**
     * Initialize the toast container.
     */
    function init() {
        if (!toastContainer) {
            toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.className = 'toast-container';
                document.body.appendChild(toastContainer);
            }
        }
    }
    
    /**
     * Create a toast element.
     * @param {string} message - The message to display
     * @param {string} type - The type of toast (success, error, info, warning)
     * @param {number} duration - Duration in milliseconds before auto-dismiss
     * @returns {HTMLElement} The created toast element
     */
    function createToastElement(message, type, duration) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Set icon based on type
        let icon = '';
        switch (type) {
            case ToastType.SUCCESS:
                icon = '✓';
                break;
            case ToastType.ERROR:
                icon = '✕';
                break;
            case ToastType.WARNING:
                icon = '⚠';
                break;
            case ToastType.INFO:
            default:
                icon = 'ℹ';
                break;
        }
        
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${escapeHtml(message)}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        return toast;
    }
    
    /**
     * Show a toast notification.
     * @param {string} message - The message to display
     * @param {string} type - The type of toast (default: info)
     * @param {number} duration - Duration in milliseconds (default: 4000)
     */
    function show(message, type = ToastType.INFO, duration = ToastConfig.DEFAULT_DURATION) {
        init();
        
        // Clamp duration
        duration = Math.max(ToastConfig.MIN_DURATION, Math.min(duration, ToastConfig.MAX_DURATION));
        
        const toast = createToastElement(message, type, duration);
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('toast-show'), 10);
        
        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                hide(toast);
            }, duration);
        }
    }
    
    /**
     * Hide and remove a toast element.
     * @param {HTMLElement} toast - The toast element to remove
     */
    function hide(toast) {
        if (toast && toast.parentElement) {
            toast.classList.remove('toast-show');
            toast.classList.add('toast-hide');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
            }, 300); // Wait for animation
        }
    }
    
    /**
     * Remove all toasts.
     */
    function clearAll() {
        if (toastContainer) {
            toastContainer.innerHTML = '';
        }
    }
    
    /**
     * Convenience methods for different toast types.
     */
    function success(message, duration) {
        show(message, ToastType.SUCCESS, duration);
    }
    
    function error(message, duration) {
        show(message, ToastType.ERROR, duration);
    }
    
    function info(message, duration) {
        show(message, ToastType.INFO, duration);
    }
    
    function warning(message, duration) {
        show(message, ToastType.WARNING, duration);
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public API
    return {
        init,
        show,
        hide,
        clearAll,
        success,
        error,
        info,
        warning
    };
})();

// Global convenience functions
function showToast(message, type, duration) {
    ToastManager.show(message, type, duration);
}

function showSuccess(message, duration) {
    ToastManager.success(message, duration);
}

function showError(message, duration) {
    ToastManager.error(message, duration);
}

function showInfo(message, duration) {
    ToastManager.info(message, duration);
}

function showWarning(message, duration) {
    ToastManager.warning(message, duration);
}