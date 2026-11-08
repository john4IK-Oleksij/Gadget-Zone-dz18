import { getToken, getRefreshToken, setToken, clearToken } from './auth.js';

// Single place for the backend URL. Automatically adapts for local Live Server and Railway production.
export const API_BASE_URL = (
    window.location.hostname === '127.0.0.1' && window.location.port === '5500'
) ? 'http://127.0.0.1:8000' : '';

export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

let refreshPromise = null;

async function refreshAccessToken() {
    if (!refreshPromise) {
        refreshPromise = (async () => {
            const refreshToken = getRefreshToken();
            let res;
            try {
                res = await fetch(`${API_BASE_URL}/auth/refresh`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ refresh_token: refreshToken }),
                });
            } catch {
                throw new ApiError('Cannot reach authentication server', 0);
            }

            if (!res.ok) {
                clearToken();
                throw new ApiError('Session expired', res.status);
            }

            const data = await res.json();
            setToken(data.access_token, data.refresh_token);
            return data.access_token;
        })().finally(() => {
            refreshPromise = null;
        });
    }
    return refreshPromise;
}

/**
 * Fetch JSON from the backend. Sends the JWT when present.
 * Throws ApiError with a user-friendly message (never a stack trace).
 */
export async function apiRequest(path, { method = 'GET', body, form, auth = true } = {}) {
    const headers = {};
    let payload;
    if (form !== undefined) {
        payload = new URLSearchParams(form);
    } else if (body !== undefined) {
        headers['Content-Type'] = 'application/json';
        payload = JSON.stringify(body);
    }
    const token = getToken();
    if (auth && token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            method,
            headers,
            body: payload,
            credentials: 'include',
        });
        window.dispatchEvent(new CustomEvent('api-health-status', { detail: { online: true } }));
    } catch {
        window.dispatchEvent(new CustomEvent('api-health-status', { detail: { online: false } }));
        throw new ApiError(`Cannot reach the server at ${API_BASE_URL}. Make sure the backend is running.`, 0);
    }

    // Auto-refresh token on 401 if auth is enabled and not already an auth endpoint
    if (response.status === 401 && auth && !path.startsWith('/auth/login') && !path.startsWith('/auth/refresh')) {
        try {
            const newToken = await refreshAccessToken();
            headers['Authorization'] = `Bearer ${newToken}`;
            response = await fetch(`${API_BASE_URL}${path}`, {
                method,
                headers,
                body: payload,
                credentials: 'include',
            });
        } catch {
            clearToken();
        }
    }

    if (response.status === 204) {
        return null;
    }

    let data = null;
    try {
        data = await response.json();
    } catch {
        // Non-JSON response: fall through to the generic message below.
    }

    if (!response.ok) {
        const message = data && typeof data.detail === 'string'
            ? data.detail
            : 'Something went wrong. Please try again.';
        throw new ApiError(message, response.status);
    }
    return data;
}

/**
 * Upload an image file from the admin device to the server.
 * Returns { image_url: "/uploads/..." }
 */
export async function apiUploadImage(file) {
    let token = getToken();
    const formData = new FormData();
    formData.append('file', file);

    let response;
    try {
        response = await fetch(`${API_BASE_URL}/products/upload-image`, {
            method: 'POST',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: formData,
            credentials: 'include',
        });
    } catch {
        throw new ApiError(`Cannot reach the server at ${API_BASE_URL}.`, 0);
    }

    if (response.status === 401) {
        try {
            const newToken = await refreshAccessToken();
            response = await fetch(`${API_BASE_URL}/products/upload-image`, {
                method: 'POST',
                headers: newToken ? { Authorization: `Bearer ${newToken}` } : {},
                body: formData,
                credentials: 'include',
            });
        } catch {
            clearToken();
        }
    }

    let data = null;
    try {
        data = await response.json();
    } catch {
        // Non-JSON response
    }

    if (!response.ok) {
        const message = data && typeof data.detail === 'string'
            ? data.detail
            : 'Failed to upload image.';
        throw new ApiError(message, response.status);
    }
    return data;
}
