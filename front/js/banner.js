import { createElement } from './ui.js';

const BANNER_TIMEOUT_MS = 4000;

function getBannerStack() {
    let stack = document.getElementById('banner-stack');
    if (!stack) {
        stack = createElement('div', 'banner-stack');
        stack.id = 'banner-stack';
        stack.setAttribute('role', 'status');
        stack.setAttribute('aria-live', 'polite');
        document.body.append(stack);
    }
    return stack;
}

/** Shows a temporary banner. `type` is "success" (green) or "error". */
export function showBanner(message, type = 'success') {
    const banner = createElement('div', `banner banner--${type}`, message);
    getBannerStack().append(banner);
    window.setTimeout(() => banner.remove(), BANNER_TIMEOUT_MS);
}

// A banner that must survive a page redirect (login / logout).
const FLASH_KEY = 'gadgetzone_flash';

export function queueBanner(message, type = 'success') {
    sessionStorage.setItem(FLASH_KEY, JSON.stringify({ message, type }));
}

export function showQueuedBanner() {
    const raw = sessionStorage.getItem(FLASH_KEY);
    if (!raw) {
        return;
    }
    sessionStorage.removeItem(FLASH_KEY);
    try {
        const { message, type } = JSON.parse(raw);
        showBanner(message, type);
    } catch {
        // Ignore a corrupted flash message.
    }
}
