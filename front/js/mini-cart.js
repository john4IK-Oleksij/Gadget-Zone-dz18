import { apiRequest } from './api.js';
import { showBanner } from './banner.js';
import {
    createElement,
    createLink,
    createProductImage,
    createCartIcon,
    detailsUrl,
    formatPrice,
} from './ui.js';

let activeDropdown = null;

function renderEmptyState(content) {
    const empty = createElement('div', 'mini-cart__empty');
    empty.append(createElement('p', 'mini-cart__empty-text', 'Your cart is empty.'));
    content.replaceChildren(empty);
}

async function removeMiniCartItem(productId, button, refresh) {
    button.disabled = true;
    try {
        await apiRequest(`/cart/items/${productId}`, { method: 'DELETE' });
        showBanner('Item removed from cart', 'success');
        window.dispatchEvent(new CustomEvent('cart-updated'));
        await refresh();
    } catch (error) {
        showBanner(error.message, 'error');
        button.disabled = false;
    }
}

function buildMiniCartRow(item, refresh) {
    const row = createElement('li', 'mini-cart__item');

    const imgLink = createLink('mini-cart__image-link', detailsUrl(item.product_id));
    imgLink.append(createProductImage(item, 'mini-cart__image'));

    const info = createElement('div', 'mini-cart__item-info');
    const title = createElement('h4', 'mini-cart__item-title');
    title.append(createLink('mini-cart__item-link', detailsUrl(item.product_id), item.title));

    const meta = createElement('div', 'mini-cart__item-meta');
    meta.textContent = `${item.quantity} \u00D7 ${formatPrice(item.price)}`;
    info.append(title, meta);

    const removeBtn = createElement('button', 'mini-cart__item-remove');
    removeBtn.type = 'button';
    removeBtn.setAttribute('aria-label', `Remove ${item.title} from cart`);
    removeBtn.textContent = '\u00D7';
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeMiniCartItem(item.product_id, removeBtn, refresh);
    });

    row.append(imgLink, info, removeBtn);
    return row;
}

function renderCartContent(dropdown, cartData, countBadge, refresh) {
    const totalItems = cartData.total_items || 0;
    if (totalItems > 0) {
        countBadge.textContent = String(totalItems);
        countBadge.hidden = false;
    } else {
        countBadge.hidden = true;
    }

    if (!cartData.items || cartData.items.length === 0) {
        renderEmptyState(dropdown);
        return;
    }

    const wrapper = createElement('div', 'mini-cart__inner');
    const list = createElement('ul', 'mini-cart__list');

    let subtotal = 0;
    cartData.items.forEach((item) => {
        list.append(buildMiniCartRow(item, refresh));
        subtotal += Number(item.price) * item.quantity;
    });

    const footer = createElement('div', 'mini-cart__footer');
    const subtotalRow = createElement('div', 'mini-cart__subtotal');
    subtotalRow.append(
        createElement('span', 'mini-cart__subtotal-label', 'Subtotal:'),
        createElement('strong', 'mini-cart__subtotal-value', formatPrice(subtotal))
    );

    const viewCartBtn = createLink('button button--primary mini-cart__btn', 'cart.html', 'View Cart');
    footer.append(subtotalRow, viewCartBtn);

    wrapper.append(list, footer);
    dropdown.replaceChildren(wrapper);
}

/**
 * Attaches the mini-cart functionality to the header cart button for authenticated users.
 */
export function setupMiniCart(wrapper) {
    const isCartPage = window.location.pathname.split('/').pop() === 'cart.html';

    const trigger = createLink('site-header__cart', 'cart.html');
    trigger.setAttribute('aria-label', 'Cart');
    if (!isCartPage) {
        trigger.setAttribute('aria-haspopup', 'true');
        trigger.setAttribute('aria-expanded', 'false');
    }
    trigger.append(createCartIcon());

    const badge = createElement('span', 'site-header__cart-badge');
    badge.hidden = true;
    trigger.append(badge);

    // On cart.html, the mini-cart dropdown popup is disabled (full cart is already on page)
    if (isCartPage) {
        wrapper.append(trigger);
        const updateBadge = async () => {
            try {
                const data = await apiRequest('/cart');
                const totalCount = (data?.items || []).reduce((sum, item) => sum + item.quantity, 0);
                if (totalCount > 0) {
                    badge.textContent = String(totalCount);
                    badge.hidden = false;
                } else {
                    badge.hidden = true;
                }
            } catch {
                badge.hidden = true;
            }
        };
        updateBadge();
        window.addEventListener('cart-updated', updateBadge);
        return;
    }

    const dropdown = createElement('div', 'mini-cart');
    dropdown.setAttribute('role', 'region');
    dropdown.setAttribute('aria-label', 'Shopping Cart Preview');
    dropdown.hidden = true;

    wrapper.append(trigger, dropdown);

    let isLoaded = false;

    const loadData = async () => {
        try {
            const data = await apiRequest('/cart');
            isLoaded = true;
            renderCartContent(dropdown, data, badge, loadData);
        } catch {
            renderEmptyState(dropdown);
        }
    };

    const openDropdown = async () => {
        if (activeDropdown && activeDropdown !== dropdown) {
            activeDropdown.hidden = true;
        }
        dropdown.hidden = false;
        trigger.setAttribute('aria-expanded', 'true');
        activeDropdown = dropdown;
        if (!isLoaded) {
            dropdown.replaceChildren(createElement('div', 'mini-cart__loading', 'Loading cart...'));
        }
        await loadData();
    };

    const closeDropdown = () => {
        dropdown.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
        if (activeDropdown === dropdown) {
            activeDropdown = null;
        }
    };

    // Initial background badge count fetch
    loadData();

    // Listen for cart modifications elsewhere on the page
    window.addEventListener('cart-updated', () => {
        loadData();
    });

    // Hover (desktop) with generous timeout and hover bridge
    let hoverTimeout = null;
    wrapper.addEventListener('mouseenter', () => {
        if (window.matchMedia('(hover: hover)').matches) {
            clearTimeout(hoverTimeout);
            openDropdown();
        }
    });
    wrapper.addEventListener('mouseleave', () => {
        if (window.matchMedia('(hover: hover)').matches) {
            clearTimeout(hoverTimeout);
            hoverTimeout = setTimeout(closeDropdown, 350);
        }
    });

    // Click / touch toggle (works on mobile and desktop)
    trigger.addEventListener('click', (event) => {
        // If clicking on mobile or without hover, toggle mini-cart
        const isHoverDevice = window.matchMedia('(hover: hover)').matches && window.innerWidth > 767;
        if (!isHoverDevice) {
            event.preventDefault();
            if (dropdown.hidden) {
                openDropdown();
            } else {
                closeDropdown();
            }
        }
    });

    // Close when clicking outside
    document.addEventListener('click', (event) => {
        if (!wrapper.contains(event.target)) {
            closeDropdown();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeDropdown();
        }
    });
}
