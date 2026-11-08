import { getToken, clearToken } from './auth.js';
import { queueBanner } from './banner.js';

const INACTIVITY_LIMIT_MS = 5 * 60 * 1000; // 5 minutes
const LAST_ACTIVITY_KEY = 'gadgetzone_last_activity';

/**
 * Tracks user activity (mouse, keyboard, touch, scroll).
 * If no activity occurs for 5 minutes, session is terminated and user is redirected to index.html.
 */
export function initInactivityTracker() {
    if (!getToken()) {
        localStorage.removeItem(LAST_ACTIVITY_KEY);
        return;
    }

    const checkInactivity = () => {
        if (!getToken()) return;
        const last = Number(localStorage.getItem(LAST_ACTIVITY_KEY) || Date.now());
        if (Date.now() - last >= INACTIVITY_LIMIT_MS) {
            clearToken();
            localStorage.removeItem(LAST_ACTIVITY_KEY);
            queueBanner('Session closed due to inactivity', 'error');

            const isHome = window.location.pathname.endsWith('index.html') ||
                           window.location.pathname.endsWith('/front/') ||
                           window.location.pathname === '/';
            if (isHome) {
                window.location.reload();
            } else {
                window.location.replace('index.html');
            }
        }
    };

    const recordActivity = () => {
        if (!getToken()) return;
        localStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()));
    };

    // Check immediately on load and set current timestamp
    checkInactivity();
    recordActivity();

    // Throttled activity listener (records at most once every 2 seconds)
    let throttleTimer = null;
    const handleAction = () => {
        if (throttleTimer) return;
        throttleTimer = setTimeout(() => {
            throttleTimer = null;
            recordActivity();
        }, 2000);
    };

    ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'].forEach((evt) => {
        window.addEventListener(evt, handleAction, { passive: true });
    });

    // Check every 10 seconds for inactivity timeout
    setInterval(checkInactivity, 10000);
}
