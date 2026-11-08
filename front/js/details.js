import { initHeader } from './header.js';
import { apiRequest } from './api.js';
import { getAuthState, ROLE } from './state.js';
import { addToCart } from './cart-actions.js';
import {
    createElement,
    createLink,
    createProductImage,
    createSoldOutBadge,
    formatPrice,
    isSoldOut,
} from './ui.js';

const container = document.getElementById('product-details');

function showMessage(text, modifier) {
    const className = modifier ? `state-message state-message--${modifier}` : 'state-message';
    container.replaceChildren(createElement('p', className, text));
}

function buildBreadcrumb(product) {
    const nav = createElement('nav', 'breadcrumb');
    nav.setAttribute('aria-label', 'Breadcrumb');
    const list = createElement('ol', 'breadcrumb__list');

    const home = createElement('li', 'breadcrumb__item');
    home.append(createLink('breadcrumb__link', 'index.html', 'Home'));

    const category = createElement('li', 'breadcrumb__item', product.category);
    const current = createElement('li', 'breadcrumb__item breadcrumb__item--current', product.title);
    current.setAttribute('aria-current', 'page');

    list.append(home, category, current);
    nav.append(list);
    return nav;
}

function buildMedia(product) {
    const media = createElement('div', 'product-details__media');
    media.append(createProductImage(product, 'product-details__image'));
    if (isSoldOut(product)) {
        media.append(createSoldOutBadge('product-details__badge'));
    }
    return media;
}

function buildMeta(product) {
    const soldOut = isSoldOut(product);
    const meta = createElement('dl', 'product-details__meta');

    const rows = [
        ['Product ID', String(product.id)],
        ['Category', product.category],
        ['Availability', soldOut ? 'Sold out' : `In stock (${product.stock_quantity} available)`],
    ];
    rows.forEach(([label, value]) => {
        const valueElement = createElement('dd', 'product-details__meta-value', value);
        if (label === 'Availability' && soldOut) {
            valueElement.classList.add('product-details__meta-value--unavailable');
        }
        meta.append(createElement('dt', 'product-details__meta-label', label), valueElement);
    });
    return meta;
}

function buildPrice(product) {
    const price = createElement('p', 'product-details__price price');
    price.append(createElement('span', 'price__current', formatPrice(product.price)));
    if (product.old_price !== null && product.old_price !== undefined) {
        price.append(createElement('span', 'price__old', formatPrice(product.old_price)));
    }
    return price;
}

function buildQuantityControl() {
    const wrapper = createElement('div', 'quantity-control');

    const minus = createElement('button', 'quantity-control__button', '\u2212');
    minus.type = 'button';
    minus.setAttribute('aria-label', 'Decrease quantity');

    const input = createElement('input', 'quantity-control__input');
    input.type = 'number';
    input.min = '1';
    input.step = '1';
    input.value = '1';
    input.setAttribute('aria-label', 'Quantity');

    const plus = createElement('button', 'quantity-control__button', '+');
    plus.type = 'button';
    plus.setAttribute('aria-label', 'Increase quantity');

    const readQuantity = () => {
        const value = Number.parseInt(input.value, 10);
        return Number.isInteger(value) && value >= 1 ? value : 1;
    };
    minus.addEventListener('click', () => {
        input.value = String(Math.max(1, readQuantity() - 1));
    });
    plus.addEventListener('click', () => {
        input.value = String(readQuantity() + 1);
    });
    input.addEventListener('change', () => {
        input.value = String(readQuantity());
    });

    wrapper.append(minus, input, plus);
    return { wrapper, readQuantity };
}

// Admin has no cart: the whole purchase block is hidden for Admin.
function buildPurchase(product, role) {
    if (role === ROLE.ADMIN) {
        return null;
    }

    const purchase = createElement('div', 'product-details__purchase');
    const soldOut = isSoldOut(product);

    if (soldOut) {
        purchase.append(createElement('p', 'product-details__unavailable', 'This product is currently unavailable.'));
    }

    const { wrapper, readQuantity } = buildQuantityControl();
    const addButton = createElement('button', 'button button--cta', 'Add to Cart');
    addButton.type = 'button';

    if (soldOut) {
        wrapper.querySelectorAll('button, input').forEach((control) => {
            control.disabled = true;
        });
        addButton.disabled = true;
    } else {
        addButton.addEventListener('click', async () => {
            addButton.disabled = true;
            await addToCart(product.id, readQuantity());
            addButton.disabled = false;
        });
    }

    const row = createElement('div', 'row');
    row.append(wrapper, addButton);
    purchase.append(row);
    return purchase;
}

function renderProduct(product, role) {
    document.title = `${product.title} | Gadget Zone`;

    const info = createElement('div', 'product-details__info');
    info.append(
        createElement('h1', 'product-details__title', product.title),
        buildPrice(product),
        buildMeta(product),
    );
    if (product.description) {
        info.append(createElement('p', 'product-details__description', product.description));
    }
    const purchase = buildPurchase(product, role);
    if (purchase) {
        info.append(purchase);
    }
    info.append(createLink('product-details__back button button--outline', 'index.html', '\u2190 Return to Shop'));

    const layout = createElement('div', 'product-details__layout');
    layout.append(buildMedia(product), info);

    container.replaceChildren(buildBreadcrumb(product), layout);
}

async function loadProduct() {
    const id = new URLSearchParams(window.location.search).get('id');
    if (!/^\d+$/.test(id ?? '')) {
        showMessage('Product not found.', 'error');
        return;
    }

    showMessage('Loading...');
    try {
        const [{ role }, product] = await Promise.all([
            getAuthState(),
            apiRequest(`/products/${id}`, { auth: false }),
        ]);
        renderProduct(product, role);
    } catch (error) {
        showMessage(error.status === 404 ? 'Product not found.' : error.message, 'error');
    }
}

initHeader();
loadProduct();
