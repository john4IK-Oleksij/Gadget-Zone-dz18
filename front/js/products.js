import { initHeader } from './header.js';
import { apiRequest } from './api.js';
import { getAuthState, ROLE } from './state.js';
import { addToCart } from './cart-actions.js';
import {
    createElement,
    createLink,
    createProductImage,
    createSoldOutBadge,
    createCartIcon,
    createEyeIcon,
    detailsUrl,
    formatPrice,
    isSoldOut,
} from './ui.js';

// The backend returns 8 products per page by default.
const PAGE_SIZE = 8;

const grid = document.getElementById('product-grid');
const paginationNav = document.getElementById('pagination');

let currentPageState = 1;
let totalPagesState = 1;

function getPageFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const p = parseInt(params.get('page'), 10);
    return Number.isInteger(p) && p > 0 ? p : 1;
}

function setPageInUrl(page) {
    const url = new URL(window.location.href);
    if (page === 1) {
        url.searchParams.delete('page');
    } else {
        url.searchParams.set('page', String(page));
    }
    window.history.pushState({ page }, '', url.toString());
}

/**
 * Custom silky-smooth slow scroll with easeInOutCubic easing.
 * Duration 750ms for a gentle, cinematic feel.
 */
function smoothScrollToTop(duration = 750) {
    const start = window.scrollY;
    if (start === 0) return;
    const distance = -start;
    let startTime = null;

    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // easeInOutCubic easing for gentle start and slow stop
        const ease = progress < 0.5
            ? 4 * progress * progress * progress
            : 1 - Math.pow(-2 * progress + 2, 3) / 2;

        window.scrollTo(0, start + distance * ease);
        if (elapsed < duration) {
            window.requestAnimationFrame(step);
        }
    }
    window.requestAnimationFrame(step);
}

function navigateToPage(newPage) {
    if (newPage < 1 || newPage > totalPagesState || newPage === currentPageState) {
        return;
    }
    setPageInUrl(newPage);
    loadProducts(newPage);
    smoothScrollToTop(750);
}

function showMessage(text, modifier) {
    const className = modifier ? `state-message state-message--${modifier}` : 'state-message';
    grid.replaceChildren(createElement('p', className, text));
}

function buildActions(product, role) {
    const actions = createElement('div', 'product-card__actions');

    const eye = createLink('product-card__action product-card__action--eye', detailsUrl(product.id));
    eye.setAttribute('aria-label', `View details: ${product.title}`);
    eye.append(createEyeIcon());
    actions.append(eye);

    // Admin has no cart; sold out products cannot be added.
    if (role !== ROLE.ADMIN && !isSoldOut(product)) {
        const cart = createElement('button', 'product-card__action product-card__action--cart');
        cart.type = 'button';
        cart.setAttribute('aria-label', `Add to cart: ${product.title}`);
        cart.append(createCartIcon());
        cart.addEventListener('click', async (e) => {
            e.stopPropagation();
            cart.disabled = true;
            await addToCart(product.id, 1);
            cart.disabled = false;
        });
        actions.append(cart);
    }
    return actions;
}

function buildPrice(product) {
    const price = createElement('p', 'product-card__price price');
    price.append(createElement('span', 'price__current', formatPrice(product.price)));
    if (product.old_price !== null && product.old_price !== undefined) {
        price.append(createElement('span', 'price__old', formatPrice(product.old_price)));
    }
    return price;
}

function buildCard(product, role) {
    const card = createElement('article', 'product-card');

    const media = createElement('div', 'product-card__media');
    const imageLink = createLink('product-card__image-link', detailsUrl(product.id));
    imageLink.tabIndex = -1;
    imageLink.setAttribute('aria-hidden', 'true');
    imageLink.append(createProductImage(product, 'product-card__image'));
    media.append(imageLink);
    if (isSoldOut(product)) {
        media.append(createSoldOutBadge('product-card__badge'));
    }
    media.append(buildActions(product, role));

    const body = createElement('div', 'product-card__body');
    const title = createElement('h3', 'product-card__title');
    title.append(createLink('product-card__title-link', detailsUrl(product.id), product.title));
    body.append(title, buildPrice(product));

    card.append(media, body);
    return card;
}

function renderPagination(currentPage, totalCount) {
    if (!paginationNav) return;
    const totalPages = Math.ceil(totalCount / PAGE_SIZE);
    totalPagesState = totalPages;
    if (totalPages <= 1) {
        paginationNav.replaceChildren();
        return;
    }

    const fragment = document.createDocumentFragment();

    // Previous Button
    const prevBtn = createElement('button', 'pagination__button', '« Prev');
    prevBtn.type = 'button';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.addEventListener('click', () => navigateToPage(currentPage - 1));
    fragment.append(prevBtn);

    // Numbered buttons with smart range
    const pages = [];
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            pages.push(i);
        } else if (pages[pages.length - 1] !== '...') {
            pages.push('...');
        }
    }

    pages.forEach((p) => {
        if (p === '...') {
            fragment.append(createElement('span', 'pagination__ellipsis', '…'));
        } else {
            const isCurrent = p === currentPage;
            const btn = createElement(
                'button',
                isCurrent ? 'pagination__button pagination__button--active' : 'pagination__button',
                String(p)
            );
            btn.type = 'button';
            if (isCurrent) {
                btn.setAttribute('aria-current', 'page');
            } else {
                btn.addEventListener('click', () => navigateToPage(p));
            }
            fragment.append(btn);
        }
    });

    // Next Button
    const nextBtn = createElement('button', 'pagination__button', 'Next »');
    nextBtn.type = 'button';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.addEventListener('click', () => navigateToPage(currentPage + 1));
    fragment.append(nextBtn);

    paginationNav.replaceChildren(fragment);
}

async function loadProducts(page = getPageFromUrl()) {
    currentPageState = page;
    showMessage('Loading...');
    try {
        const skip = (page - 1) * PAGE_SIZE;
        const [{ role }, products, countData] = await Promise.all([
            getAuthState(),
            apiRequest(`/products?skip=${skip}&limit=${PAGE_SIZE}`, { auth: false }),
            apiRequest('/products/count', { auth: false }).catch(() => ({ count: 0 })),
        ]);

        if (products.length === 0) {
            showMessage('No products found on this page.');
            if (paginationNav) paginationNav.replaceChildren();
            return;
        }

        grid.replaceChildren(...products.map((product) => buildCard(product, role)));
        renderPagination(page, countData.count);
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 1. Browser navigation (Back / Forward)
window.addEventListener('popstate', (e) => {
    const page = (e.state && e.state.page) || getPageFromUrl();
    loadProducts(page);
});

// 2. Keyboard Arrow Left / Right navigation
window.addEventListener('keydown', (e) => {
    const active = document.activeElement;
    if (active && ['INPUT', 'TEXTAREA', 'SELECT'].includes(active.tagName)) {
        return;
    }
    if (e.key === 'ArrowLeft') {
        if (currentPageState > 1) {
            e.preventDefault();
            navigateToPage(currentPageState - 1);
        }
    } else if (e.key === 'ArrowRight') {
        if (currentPageState < totalPagesState) {
            e.preventDefault();
            navigateToPage(currentPageState + 1);
        }
    }
});

// 3. Touch swipe gesture (Mobile)
let touchStartX = 0;
let touchStartY = 0;

grid.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    }
}, { passive: true });

grid.addEventListener('touchend', (e) => {
    if (e.changedTouches.length === 1) {
        const diffX = e.changedTouches[0].clientX - touchStartX;
        const diffY = e.changedTouches[0].clientY - touchStartY;
        // Horizontal swipe must dominate vertical scroll
        if (Math.abs(diffX) > 60 && Math.abs(diffX) > Math.abs(diffY) * 1.5) {
            if (diffX < 0) {
                navigateToPage(currentPageState + 1);
            } else {
                navigateToPage(currentPageState - 1);
            }
        }
    }
}, { passive: true });

// 4. Mouse Grab & Drag gesture (Desktop)
let isMouseDown = false;
let mouseStartX = 0;
let mouseStartY = 0;
let hasDragged = false;

grid.addEventListener('mousedown', (e) => {
    if (e.button !== 0 || e.target.closest('button')) return;
    isMouseDown = true;
    hasDragged = false;
    mouseStartX = e.clientX;
    mouseStartY = e.clientY;
});

window.addEventListener('mousemove', (e) => {
    if (!isMouseDown) return;
    const diffX = e.clientX - mouseStartX;
    if (Math.abs(diffX) > 12) {
        hasDragged = true;
        grid.classList.add('product-grid--grabbing');
    }
});

window.addEventListener('mouseup', (e) => {
    if (!isMouseDown) return;
    const diffX = e.clientX - mouseStartX;
    const diffY = e.clientY - mouseStartY;
    isMouseDown = false;
    grid.classList.remove('product-grid--grabbing');

    if (hasDragged && Math.abs(diffX) > 75 && Math.abs(diffX) > Math.abs(diffY)) {
        if (diffX < 0) {
            navigateToPage(currentPageState + 1);
        } else {
            navigateToPage(currentPageState - 1);
        }
    }
});

// Suppress click on card links if dragging was performed
grid.addEventListener('click', (e) => {
    if (hasDragged) {
        e.preventDefault();
        e.stopPropagation();
        hasDragged = false;
    }
}, true);

initHeader();
loadProducts();
