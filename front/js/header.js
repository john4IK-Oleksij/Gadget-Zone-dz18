import { getAuthState, ROLE } from './state.js';
import { clearToken } from './auth.js';
import { API_BASE_URL } from './api.js';
import { createElement, createLink, createCartIcon } from './ui.js';
import { queueBanner, showQueuedBanner } from './banner.js';
import { setupMiniCart } from './mini-cart.js';
import { initInactivityTracker } from './inactivity.js';

const MOBILE_BREAKPOINT_PX = 767;

function buildLogo() {
    const logo = createLink('site-header__logo', 'index.html');
    logo.setAttribute('aria-label', 'GadgetZone - Home');
    const icon = createElement('img', 'site-header__logo-icon');
    icon.src = 'static/images/logo-icon1.png';
    icon.alt = '';
    icon.width = 32;
    icon.height = 32;

    const healthDot = createElement('span', 'api-health api-health--loading');
    healthDot.setAttribute('aria-label', 'API Status');
    healthDot.title = 'API Status: checking...';

    const setHealth = (online) => {
        if (online) {
            healthDot.className = 'api-health api-health--online';
            healthDot.title = 'API Status: Online (connected)';
        } else {
            healthDot.className = 'api-health api-health--offline';
            healthDot.title = 'API Status: Offline (cannot reach server)';
        }
    };

    const ping = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/db-test`, { method: 'GET' });
            setHealth(res.ok);
        } catch {
            setHealth(false);
        }
    };

    ping();
    setInterval(ping, 20000);

    window.addEventListener('api-health-status', (e) => {
        setHealth(Boolean(e.detail?.online));
    });

    logo.append(icon, createElement('span', 'site-header__logo-text', 'GadgetZone'), healthDot);
    return logo;
}

function buildBurger() {
    const burger = createElement('button', 'site-header__burger');
    burger.type = 'button';
    burger.setAttribute('aria-label', 'Toggle menu');
    burger.setAttribute('aria-expanded', 'false');
    burger.setAttribute('aria-controls', 'site-header-menu');
    for (let i = 0; i < 3; i += 1) {
        burger.append(createElement('span', 'site-header__burger-line'));
    }
    return burger;
}

function buildNav(role, currentPage) {
    const nav = createElement('nav', 'site-header__nav');
    nav.setAttribute('aria-label', 'Main navigation');

    const items = [{ href: 'index.html', text: 'Shop' }];
    if (role === ROLE.ADMIN || role === ROLE.MANAGER) {
        items.push({ href: 'admin.html', text: role === ROLE.ADMIN ? 'Admin' : 'Management' });
    }

    items.forEach((item) => {
        const link = createLink('site-header__nav-link', item.href, item.text);
        if (item.href === currentPage) {
            link.classList.add('site-header__nav-link--active');
            link.setAttribute('aria-current', 'page');
        }
        nav.append(link);
    });
    return nav;
}

// UI only: real search is not supported by the backend yet.
function buildSearch() {
    const form = createElement('form', 'site-header__search');
    form.setAttribute('role', 'search');
    form.addEventListener('submit', (event) => event.preventDefault());

    const input = createElement('input', 'site-header__search-input');
    input.type = 'search';
    input.placeholder = 'Search products';
    input.setAttribute('aria-label', 'Search products');
    form.append(input);
    return form;
}

function buildActions(role, user) {
    const actions = createElement('div', 'site-header__actions');

    if (role === ROLE.USER) {
        const cartWrapper = createElement('div', 'site-header__cart-wrapper');
        setupMiniCart(cartWrapper);
        actions.append(cartWrapper);
    }

    if (role === ROLE.GUEST) {
        actions.append(createLink('site-header__account-link', 'login.html', 'Login / Sign Up'));
        return actions;
    }

    actions.append(createElement('span', 'site-header__email', user.email));

    const logout = createElement('button', 'site-header__logout', 'Logout');
    logout.type = 'button';
    logout.addEventListener('click', () => {
        clearToken();
        queueBanner('You have been logged out.', 'success');
        window.location.href = 'index.html';
    });
    actions.append(logout);
    return actions;
}

function setupBurger(header, burger) {
    const setOpen = (isOpen) => {
        header.classList.toggle('site-header--open', isOpen);
        burger.setAttribute('aria-expanded', String(isOpen));
    };

    burger.addEventListener('click', (event) => {
        event.stopPropagation();
        setOpen(!header.classList.contains('site-header--open'));
    });

    document.addEventListener('click', (event) => {
        if (!header.contains(event.target)) {
            setOpen(false);
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && header.classList.contains('site-header--open')) {
            setOpen(false);
        }
    });

    header.querySelectorAll('.site-header__nav-link').forEach((link) => {
        link.addEventListener('click', () => setOpen(false));
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > MOBILE_BREAKPOINT_PX) {
            setOpen(false);
        }
    });
}

/** Renders the shared header into #site-header. Called by every page module. */
export async function initHeader() {
    const header = document.getElementById('site-header');
    if (!header) {
        return;
    }

    showQueuedBanner();
    const { role, user } = await getAuthState();
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    const inner = createElement('div', 'site-header__inner');
    const burger = buildBurger();
    const menu = createElement('div', 'site-header__menu');
    menu.id = 'site-header-menu';
    menu.append(buildNav(role, currentPage), buildSearch());

    inner.append(burger, buildLogo(), menu, buildActions(role, user));
    header.replaceChildren(inner);
    header.dataset.role = role;

    setupBurger(header, burger);
    initInactivityTracker();
}
