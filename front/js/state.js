import { apiRequest } from './api.js';
import { getToken, clearToken } from './auth.js';

export const ROLE = Object.freeze({
    GUEST: 'guest',
    USER: 'user',
    MANAGER: 'manager',
    ADMIN: 'admin',
});

let authStatePromise = null;

/**
 * Central auth state: role (guest / user / manager / admin) and current user.
 * Role checks only drive the UI; the backend is the real security boundary.
 */
export function getAuthState() {
    if (!authStatePromise) {
        authStatePromise = loadAuthState();
    }
    return authStatePromise;
}

export function resetAuthState() {
    authStatePromise = null;
}

async function loadAuthState() {
    if (!getToken()) {
        return { role: ROLE.GUEST, user: null };
    }
    try {
        const user = await apiRequest('/users/me');
        let role = ROLE.USER;
        if (user.role === 'admin' || user.is_admin) {
            role = ROLE.ADMIN;
        } else if (user.role === 'manager') {
            role = ROLE.MANAGER;
        }
        return { role, user };
    } catch (error) {
        // Invalid or expired token: act as guest. Keep the token on network errors.
        if (error.status === 401 || error.status === 403) {
            clearToken();
        }
        return { role: ROLE.GUEST, user: null };
    }
}
