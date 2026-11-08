// JWT storage. Login/register flows are implemented in Iteration 6.
const TOKEN_KEY = 'gadgetzone_token';
const REFRESH_TOKEN_KEY = 'gadgetzone_refresh_token';

export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setToken(token, refreshToken = null) {
    if (token) {
        localStorage.setItem(TOKEN_KEY, token);
    }
    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/** Sends the visitor to the login page and remembers the current page to return to. */
export function redirectToLogin() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const next = encodeURIComponent(`${currentPage}${window.location.search}`);
    window.location.href = `login.html?next=${next}`;
}
