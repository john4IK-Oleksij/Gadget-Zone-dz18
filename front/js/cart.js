import { initHeader } from './header.js';
import { apiRequest } from './api.js';
import { getAuthState, ROLE } from './state.js';
import { redirectToLogin } from './auth.js';
import { showBanner } from './banner.js';
import {
    createElement,
    createLink,
    createProductImage,
    createSoldOutBadge,
    detailsUrl,
    formatPrice,
} from './ui.js';

const container = document.getElementById('cart');

function showMessage(text, modifier) {
    const className = modifier ? `state-message state-message--${modifier}` : 'state-message';
    container.replaceChildren(createElement('p', className, text));
}

function renderEmptyCart() {
    const empty = createElement('div', 'cart__empty stack');
    empty.append(
        createElement('p', 'state-message', 'Your cart is empty.'),
        createLink('button button--outline cart__return', 'index.html', '\u2190 Return to Shop')
    );
    container.replaceChildren(empty);
}

function renderAdminNotice() {
    const notice = createElement('div', 'cart__empty stack');
    notice.append(
        createElement('p', 'state-message', 'Admins do not have a shopping cart.'),
        createLink('button button--primary cart__return', 'index.html', 'Return to Shop')
    );
    container.replaceChildren(notice);
}

async function updateItemQuantity(productId, newQuantity, controls) {
    controls.forEach((c) => (c.disabled = true));
    try {
        await apiRequest(`/cart/items/${productId}`, {
            method: 'PATCH',
            body: { quantity: newQuantity },
        });
        await loadCart();
    } catch (error) {
        showBanner(error.message, 'error');
        controls.forEach((c) => (c.disabled = false));
    }
}

async function removeItem(productId, button) {
    button.disabled = true;
    try {
        await apiRequest(`/cart/items/${productId}`, {
            method: 'DELETE',
        });
        showBanner('Item removed from cart', 'success');
        await loadCart();
    } catch (error) {
        showBanner(error.message, 'error');
        button.disabled = false;
    }
}

function buildCartItemRow(item) {
    const row = createElement('article', 'cart-item card');
    const isDiscontinued = item.is_active === false;
    const isUnavailable = item.stock_quantity === 0 || isDiscontinued;

    if (isDiscontinued) {
        row.classList.add('cart-item--discontinued');
    }

    // 1. Media
    const media = createElement('div', 'cart-item__media');
    const imgLink = createLink('cart-item__image-link', detailsUrl(item.product_id));
    imgLink.append(createProductImage(item, 'cart-item__image'));
    media.append(imgLink);
    if (isDiscontinued) {
        media.append(createElement('span', 'badge badge--danger cart-item__badge', 'Знято з продажу'));
    } else if (isUnavailable) {
        media.append(createSoldOutBadge('cart-item__badge'));
    }

    // 2. Info: Title & Price
    const info = createElement('div', 'cart-item__info');
    const title = createElement('h2', 'cart-item__title');
    title.append(createLink('cart-item__title-link', detailsUrl(item.product_id), item.title));
    info.append(title);

    if (isDiscontinued) {
        info.append(createElement('span', 'cart-item__badge-discontinued', 'Знято з продажу'));
    } else if (isUnavailable) {
        info.append(createElement('span', 'cart-item__unavailable-text', 'Unavailable (out of stock)'));
    }

    const price = createElement('div', 'cart-item__price price');
    price.append(createElement('span', 'price__current', formatPrice(item.price)));
    if (item.old_price) {
        price.append(createElement('span', 'price__old', formatPrice(item.old_price)));
    }
    info.append(price);

    // 3. Quantity control
    const qtyWrapper = createElement('div', 'quantity-control cart-item__quantity');
    const minus = createElement('button', 'quantity-control__button', '\u2212');
    minus.type = 'button';
    minus.setAttribute('aria-label', 'Decrease quantity');

    const qtyInput = createElement('input', 'quantity-control__input');
    qtyInput.type = 'number';
    qtyInput.min = '1';
    qtyInput.value = String(item.quantity);
    qtyInput.setAttribute('aria-label', `Quantity for ${item.title}`);

    const plus = createElement('button', 'quantity-control__button', '+');
    plus.type = 'button';
    plus.setAttribute('aria-label', 'Increase quantity');

    if (isDiscontinued) {
        minus.disabled = true;
        qtyInput.disabled = true;
        plus.disabled = true;
    }

    const allControls = [minus, qtyInput, plus];

    minus.addEventListener('click', () => {
        if (item.quantity > 1) {
            updateItemQuantity(item.product_id, item.quantity - 1, allControls);
        }
    });
    plus.addEventListener('click', () => {
        updateItemQuantity(item.product_id, item.quantity + 1, allControls);
    });
    qtyInput.addEventListener('change', () => {
        const val = Number.parseInt(qtyInput.value, 10);
        if (Number.isInteger(val) && val >= 1 && val !== item.quantity) {
            updateItemQuantity(item.product_id, val, allControls);
        } else {
            qtyInput.value = String(item.quantity);
        }
    });
    qtyWrapper.append(minus, qtyInput, plus);

    // 4. Subtotal
    const subtotalAmount = Number(item.price) * item.quantity;
    const subtotal = createElement('div', 'cart-item__subtotal');
    subtotal.append(
        createElement('span', 'cart-item__subtotal-label', 'Subtotal: '),
        createElement('strong', 'cart-item__subtotal-value', formatPrice(subtotalAmount))
    );

    // 5. Remove button (×)
    const removeBtn = createElement('button', 'cart-item__remove');
    removeBtn.type = 'button';
    removeBtn.setAttribute('aria-label', `Remove ${item.title} from cart`);
    removeBtn.textContent = '\u00D7';
    removeBtn.addEventListener('click', () => removeItem(item.product_id, removeBtn));

    row.append(media, info, qtyWrapper, subtotal, removeBtn);
    return { row, subtotalAmount };
}

function renderCart(cartData) {
    if (!cartData.items || cartData.items.length === 0) {
        renderEmptyCart();
        return;
    }

    const cartWrapper = createElement('div', 'cart__content stack');
    const itemsList = createElement('div', 'cart__items stack');

    let totalAmount = 0;
    cartData.items.forEach((item) => {
        const { row, subtotalAmount } = buildCartItemRow(item);
        itemsList.append(row);
        totalAmount += subtotalAmount;
    });

    const summary = createElement('aside', 'cart__summary card');
    const summaryBody = createElement('div', 'card__body stack');

    const totalRow = createElement('div', 'cart__total-row');
    totalRow.append(
        createElement('span', 'cart__total-label', 'Total:'),
        createElement('span', 'cart__total-value', formatPrice(totalAmount))
    );

    const returnBtn = createLink('button button--outline cart__return-btn', 'index.html', '\u2190 Return to Shop');

    summaryBody.append(totalRow, returnBtn);
    summary.append(summaryBody);

    cartWrapper.append(itemsList, summary);
    container.replaceChildren(cartWrapper);
}

async function loadCart() {
    showMessage('Loading cart...');
    try {
        const cartData = await apiRequest('/cart');
        renderCart(cartData);
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function init() {
    initHeader();
    const { role } = await getAuthState();

    if (role === ROLE.GUEST) {
        redirectToLogin();
        return;
    }
    if (role === ROLE.ADMIN) {
        renderAdminNotice();
        return;
    }

    await loadCart();
}

init();
