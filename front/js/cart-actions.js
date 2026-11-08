import { apiRequest } from './api.js';
import { redirectToLogin } from './auth.js';
import { getAuthState, ROLE } from './state.js';
import { showBanner } from './banner.js';

/**
 * Add-to-cart flow shared by the shop and details pages.
 * Guest -> login page. Admin has no cart. User -> backend cart.
 * Returns true when the item was added.
 */
export async function addToCart(productId, quantity = 1) {
    const { role } = await getAuthState();

    if (role === ROLE.GUEST) {
        redirectToLogin();
        return false;
    }
    if (role === ROLE.ADMIN) {
        return false;
    }

    try {
        await apiRequest('/cart/items', {
            method: 'POST',
            body: { product_id: productId, quantity },
        });
        showBanner('Added to cart', 'success');
        window.dispatchEvent(new CustomEvent('cart-updated'));
        return true;
    } catch (error) {
        showBanner(error.message, 'error');
        return false;
    }
}
