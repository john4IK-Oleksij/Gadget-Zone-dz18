import { API_BASE_URL } from './api.js';

export function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
        element.className = className;
    }
    if (text !== undefined) {
        element.textContent = text;
    }
    return element;
}

export function createLink(className, href, text) {
    const link = createElement('a', className, text);
    link.href = href;
    return link;
}

/** "$1399" for whole numbers, "$1399.50" otherwise. Prices arrive from the API as strings. */
export function formatPrice(value) {
    const amount = Number(value);
    if (!Number.isFinite(amount)) {
        return '';
    }
    return `$${Number.isInteger(amount) ? amount : amount.toFixed(2)}`;
}

function resolveImageUrl(image) {
    if (/^(https?:|data:)/i.test(image)) {
        return image;
    }
    if (image.startsWith('/')) {
        return `${API_BASE_URL}${image}`;
    }
    return image;
}

/**
 * Product image, or a placeholder background when the image is missing or fails to load,
 * so the image area always keeps its size.
 * `className` is the BEM element class for the image, e.g. "product-card__image".
 */
export function createProductImage(product, className) {
    const createPlaceholder = () => createElement('div', `media-placeholder ${className}`);

    if (!product.image) {
        return createPlaceholder();
    }

    const image = createElement('img', className);
    image.src = resolveImageUrl(product.image);
    image.alt = product.title;
    image.loading = 'lazy';
    image.addEventListener('error', () => image.replaceWith(createPlaceholder()), { once: true });
    return image;
}

export function createSoldOutBadge(className) {
    return createElement('span', `badge badge--sold-out ${className}`, 'Sold out');
}

export function detailsUrl(productId) {
    return `details.html?id=${encodeURIComponent(productId)}`;
}

export function isSoldOut(product) {
    return product.stock_quantity === 0;
}

const SVG_NS = 'http://www.w3.org/2000/svg';

function createIcon(shapes) {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('width', '24');
    svg.setAttribute('height', '24');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    shapes.forEach(({ tag, attributes }) => {
        const shape = document.createElementNS(SVG_NS, tag);
        Object.entries(attributes).forEach(([name, value]) => shape.setAttribute(name, value));
        svg.append(shape);
    });
    return svg;
}

export function createCartIcon() {
    return createIcon([
        { tag: 'path', attributes: { d: 'M3 4h2l2.4 11h10.2L20 7H6.2' } },
        { tag: 'circle', attributes: { cx: '9', cy: '20', r: '1.5' } },
        { tag: 'circle', attributes: { cx: '17', cy: '20', r: '1.5' } },
    ]);
}

export function createEyeIcon() {
    return createIcon([
        { tag: 'path', attributes: { d: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' } },
        { tag: 'circle', attributes: { cx: '12', cy: '12', r: '3' } },
    ]);
}
export function createEyeOffIcon() {
    return createIcon([
        { tag: 'path', attributes: { d: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' } },
        { tag: 'circle', attributes: { cx: '12', cy: '12', r: '3' } },
        { tag: 'line', attributes: { x1: '3', y1: '21', x2: '21', y2: '3' } },
    ]);
}
