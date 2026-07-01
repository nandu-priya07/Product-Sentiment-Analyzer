/**
 * Product Sentiment Analyzer - Loading Animation Module
 * Handles loading spinners and animations
 */

// Show loading spinner
function showLoading() {
    const loading = document.getElementById('loadingSpinner');
    if (loading) {
        loading.style.display = 'block';
    }
}

// Hide loading spinner
function hideLoading() {
    const loading = document.getElementById('loadingSpinner');
    if (loading) {
        loading.style.display = 'none';
    }
}

// Show loading overlay with message
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    `;
    
    overlay.innerHTML = `
        <div class="text-center text-white">
            <div class="spinner-border spinner-border-lg mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="h5">${message}</p>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

// Hide loading overlay
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Add loading class to button
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Loading...
        `;
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || 'Submit';
    }
}

// Skeleton loader for content
function showSkeletonLoader(elementId, count = 3) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `
            <div class="card mb-3" aria-hidden="true">
                <div class="card-body">
                    <div class="placeholder-glow">
                        <span class="placeholder col-6"></span>
                        <span class="placeholder col-7"></span>
                        <span class="placeholder col-4"></span>
                    </div>
                </div>
            </div>
        `;
    }
    element.innerHTML = html;
}

// Pulse animation for elements
function addPulseAnimation(element) {
    element.style.animation = 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite';
}

function removePulseAnimation(element) {
    element.style.animation = 'none';
}

// Define pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
`;
document.head.appendChild(style);

// Automatic show/hide on fetch requests
document.addEventListener('DOMContentLoaded', function() {
    // Intercept fetch requests to show/hide loading
    const originalFetch = window.fetch;
    
    window.fetch = function(...args) {
        showLoading();
        return originalFetch.apply(this, args)
            .then(response => {
                hideLoading();
                return response;
            })
            .catch(error => {
                hideLoading();
                throw error;
            });
    };
});
