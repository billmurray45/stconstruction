/**
 * CSRF Protection Utilities
 *
 * HTML формы БЕЗ файлов работают автоматически через hidden поля.
 * HTML формы С ФАЙЛАМИ (multipart/form-data) обрабатываются через fetch с header.
 */

/**
 * Get CSRF token from hidden input in the current page
 * @returns {string} CSRF token value
 */
function getCsrfToken() {
    // Try to find csrf_token in any form on the page
    const tokenInput = document.querySelector('input[name="csrf_token"]');
    if (tokenInput) {
        return tokenInput.value;
    }

    // Fallback: try to get from meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }

    console.warn('[CSRF] CSRF token not found on page');
    return '';
}

/**
 * Enhanced fetch with automatic CSRF token injection for AJAX requests
 * Use this for all AJAX POST/PUT/DELETE requests
 *
 * Example:
 *   fetchWithCsrf('/api/data', {
 *       method: 'POST',
 *       headers: { 'Content-Type': 'application/json' },
 *       body: JSON.stringify({key: 'value'})
 *   });
 *
 * @param {string} url - Request URL
 * @param {object} options - Fetch options
 * @returns {Promise} Fetch promise
 */
async function fetchWithCsrf(url, options = {}) {
    options.headers = options.headers || {};

    // Add CSRF token header for non-GET requests
    if (options.method && options.method.toUpperCase() !== 'GET') {
        const csrfToken = getCsrfToken();

        if (csrfToken) {
            // Add x-csrf-token header for AJAX requests
            options.headers['x-csrf-token'] = csrfToken;
        } else {
            console.error('[CSRF] Token not found - request may fail');
        }
    }

    return fetch(url, options);
}

/**
 * Автоматическая обработка форм с файлами через fetch
 * Формы с enctype="multipart/form-data" перехватываются и отправляются через fetch
 */
function initMultipartFormHandling() {
    document.addEventListener('submit', async function(e) {
        const form = e.target;

        // Проверяем что это форма с multipart/form-data
        if (!form || form.enctype !== 'multipart/form-data') {
            return;  // Обычные формы работают нативно
        }

        // Это форма с файлами - обрабатываем через fetch
        e.preventDefault();

        const csrfToken = getCsrfToken();
        if (!csrfToken) {
            console.error('[CSRF] Token not found for file upload form');
            alert('CSRF token not found. Please reload the page.');
            return;
        }

        const formData = new FormData(form);
        let action = form.action || window.location.href;

        // Ensure HTTPS protocol if page is loaded over HTTPS
        if (window.location.protocol === 'https:' && action.startsWith('http://')) {
            action = action.replace('http://', 'https://');
        }

        const method = form.method.toUpperCase() || 'POST';

        try {
            const response = await fetch(action, {
                method: method,
                headers: {
                    'x-csrf-token': csrfToken,  // CSRF через header для multipart
                },
                body: formData,
                redirect: 'follow'
            });

            if (response.redirected) {
                window.location.href = response.url;
            } else if (response.ok) {
                window.location.reload();
            } else {
                const text = await response.text();
                console.error('[CSRF] Form submission failed:', response.status, text.substring(0, 200));
                alert('Ошибка при отправке формы. Проверьте консоль.');
            }
        } catch (error) {
            console.error('[CSRF] Form submission error:', error);
            alert('Ошибка: ' + error.message);
        }
    });
}

// Автоинициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMultipartFormHandling);
} else {
    initMultipartFormHandling();
}

// Export for use in modules (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCsrfToken,
        fetchWithCsrf
    };
}
