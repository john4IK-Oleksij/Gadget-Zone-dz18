import { initHeader } from './header.js';
import { apiRequest, apiUploadImage, API_BASE_URL } from './api.js';
import { getAuthState, ROLE } from './state.js';
import { showBanner, queueBanner } from './banner.js';
import {
    createElement,
    createLink,
    createProductImage,
    createSoldOutBadge,
    detailsUrl,
    formatPrice,
    isSoldOut,
} from './ui.js';

const container = document.getElementById('admin');

function handleAuthError(error) {
    if (error && (error.status === 401 || error.status === 403)) {
        queueBanner('Your session has expired. Please sign in as an administrator.', 'error');
        window.location.replace('index.html');
        return true;
    }
    return false;
}

function showMessage(text, modifier) {
    const className = modifier ? `state-message state-message--${modifier}` : 'state-message';
    container.replaceChildren(createElement('p', className, text));
}

function renderAccessDenied() {
    const denied = createElement('div', 'admin__denied stack');
    denied.append(
        createElement('h2', 'admin__denied-title', 'Access Denied'),
        createElement('p', 'state-message state-message--error', 'You must be signed in as an administrator to view this area.'),
        createLink('button button--primary admin__return-btn', 'index.html', 'Return to Shop')
    );
    container.replaceChildren(denied);
}

// ----------------- DASHBOARD -----------------
async function loadDashboardStats(statsGrid) {
    statsGrid.replaceChildren(createElement('div', 'state-message', 'Loading statistics...'));
    try {
        const stats = await apiRequest('/admin/stats');
        statsGrid.replaceChildren(
            createStatCard('Total Users', stats.users_count),
            createStatCard('Total Products', stats.products_count)
        );
    } catch (error) {
        if (handleAuthError(error)) return;
        statsGrid.replaceChildren(createElement('div', 'state-message state-message--error', error.message));
    }
}

function createStatCard(label, value) {
    const card = createElement('div', 'admin-stat card');
    const body = createElement('div', 'card__body admin-stat__body');
    body.append(
        createElement('span', 'admin-stat__label', label),
        createElement('strong', 'admin-stat__value', String(value))
    );
    card.append(body);
    return card;
}

// ----------------- USERS -----------------
async function loadUsers(usersContainer, currentUser, onUserChanged) {
    usersContainer.replaceChildren(createElement('div', 'state-message', 'Loading users...'));
    try {
        const users = await apiRequest('/admin/users');
        if (!users || users.length === 0) {
            usersContainer.replaceChildren(createElement('div', 'state-message', 'No users found.'));
            return;
        }

        const tableWrapper = createElement('div', 'admin-table-wrapper card');
        const table = createElement('table', 'admin-table');
        const thead = createElement('thead');
        const headerRow = createElement('tr');
        ['#', 'Email', 'Role (RBAC)', 'Status', 'Actions'].forEach((h) => headerRow.append(createElement('th', '', h)));
        thead.append(headerRow);

        const tbody = createElement('tbody');
        users.forEach((u, index) => {
            const tr = createElement('tr');
            const isOwner = (u.id === 2 || u.email === 'alosi4ek@gmail.com');
            const isCurrent = (currentUser && u.id === currentUser.id);

            // Role column
            const tdRole = createElement('td');
            if (isOwner) {
                const ownerBadge = createElement('span', 'badge badge--admin', 'Admin (Owner)');
                tdRole.append(ownerBadge);
            } else {
                const roleSelect = createElement('select', 'form-field__input admin-table__role-select');
                roleSelect.style.padding = '4px 8px';
                roleSelect.style.fontSize = '13px';
                [
                    { value: 'customer', label: 'Customer' },
                    { value: 'manager', label: 'Manager' },
                    { value: 'admin', label: 'Admin' },
                ].forEach((opt) => {
                    const optElem = document.createElement('option');
                    optElem.value = opt.value;
                    optElem.textContent = opt.label;
                    roleSelect.append(optElem);
                });
                roleSelect.value = u.role || (u.is_admin ? 'admin' : 'customer');
                if (isCurrent) {
                    roleSelect.disabled = true;
                    roleSelect.title = 'Cannot change your own role';
                }

                roleSelect.addEventListener('change', async () => {
                    const newRole = roleSelect.value;
                    try {
                        await apiRequest(`/admin/users/${u.id}`, {
                            method: 'PATCH',
                            body: { role: newRole },
                        });
                        showBanner(`Role for ${u.email} changed to ${newRole}`, 'success');
                        if (onUserChanged) onUserChanged();
                    } catch (err) {
                        showBanner(err.message || 'Failed to update role', 'error');
                        if (onUserChanged) onUserChanged();
                    }
                });
                tdRole.append(roleSelect);
            }

            // Status column
            const tdStatus = createElement('td');
            const statusBadge = createElement(
                'span',
                `badge ${u.is_active ? 'badge--active' : 'badge--blocked'}`,
                u.is_active ? 'Active' : 'Blocked'
            );
            tdStatus.append(statusBadge);

            // Actions column
            const tdActions = createElement('td');
            const actionsBox = createElement('div', 'admin-table__actions');

            if (isOwner) {
                const protectedLabel = createElement('span', 'text-muted', 'Owner (Immutable)');
                protectedLabel.style.fontSize = '12px';
                actionsBox.append(protectedLabel);
            } else if (isCurrent) {
                const youLabel = createElement('span', 'text-muted', 'You (Current Admin)');
                youLabel.style.fontSize = '12px';
                actionsBox.append(youLabel);
            } else {
                // Toggle Block/Unblock
                const blockBtn = createElement(
                    'button',
                    `button ${u.is_active ? 'button--danger' : 'button--outline'} admin-table__action-btn`,
                    u.is_active ? 'Block' : 'Unblock'
                );
                blockBtn.type = 'button';
                blockBtn.addEventListener('click', async () => {
                    const targetState = !u.is_active;
                    try {
                        await apiRequest(`/admin/users/${u.id}`, {
                            method: 'PATCH',
                            body: { is_active: targetState },
                        });
                        showBanner(
                            `User ${u.email} ${targetState ? 'unblocked' : 'blocked (sessions revoked)'}`,
                            targetState ? 'success' : 'info'
                        );
                        if (onUserChanged) onUserChanged();
                    } catch (err) {
                        showBanner(err.message || 'Failed to update user status', 'error');
                    }
                });

                // Delete Button
                const delBtn = createElement('button', 'button button--danger admin-table__action-btn', 'Delete');
                delBtn.type = 'button';
                delBtn.addEventListener('click', async () => {
                    if (!window.confirm(`Are you sure you want to permanently delete user ${u.email}?`)) {
                        return;
                    }
                    try {
                        await apiRequest(`/admin/users/${u.id}`, { method: 'DELETE' });
                        showBanner(`User ${u.email} deleted`, 'info');
                        if (onUserChanged) onUserChanged();
                    } catch (err) {
                        showBanner(err.message || 'Failed to delete user', 'error');
                    }
                });

                actionsBox.append(blockBtn, delBtn);
            }

            tdActions.append(actionsBox);

            tr.append(
                createElement('td', 'admin-table__id', String(index + 1)),
                createElement('td', '', u.email),
                tdRole,
                tdStatus,
                tdActions
            );
            tbody.append(tr);
        });

        table.append(thead, tbody);
        tableWrapper.append(table);
        usersContainer.replaceChildren(tableWrapper);
    } catch (error) {
        if (handleAuthError(error)) return;
        usersContainer.replaceChildren(createElement('div', 'state-message state-message--error', error.message));
    }
}

// ----------------- PRODUCTS CRUD -----------------
const EDITING_STORAGE_KEY = 'gadgetzone_admin_editing';
let currentEditingProduct = null;

function buildProductForm(formCard, onSaved, onCancel) {
    formCard.replaceChildren();

    const isEdit = currentEditingProduct !== null;
    const title = createElement('h3', 'admin-form__title', isEdit ? `Edit Product #${currentEditingProduct.id}` : 'Create New Product');

    const form = createElement('form', 'admin-form stack');

    // ID field (read-only when editing)
    if (isEdit) {
        const idField = createElement('div', 'form-field');
        const idLabel = createElement('label', 'form-field__label', 'Product ID (read-only)');
        const idInput = createElement('input', 'form-field__input');
        idInput.type = 'text';
        idInput.value = String(currentEditingProduct.id);
        idInput.disabled = true;
        idField.append(idLabel, idInput);
        form.append(idField);
    }

    // Title
    const titleField = createElement('div', 'form-field');
    const titleLabel = createElement('label', 'form-field__label', 'Title *');
    const titleInput = createElement('input', 'form-field__input');
    titleInput.type = 'text';
    titleInput.required = true;
    titleInput.value = isEdit ? currentEditingProduct.title : '';
    titleField.append(titleLabel, titleInput);

    // Description
    const descField = createElement('div', 'form-field');
    const descLabel = createElement('label', 'form-field__label', 'Description *');
    const descInput = createElement('textarea', 'form-field__input admin-form__textarea');
    descInput.rows = 3;
    descInput.required = true;
    descInput.value = isEdit ? currentEditingProduct.description : '';
    descField.append(descLabel, descInput);

    // Category
    const catField = createElement('div', 'form-field');
    const catLabel = createElement('label', 'form-field__label', 'Category *');
    const catInput = createElement('input', 'form-field__input');
    catInput.type = 'text';
    catInput.required = true;
    catInput.value = isEdit ? currentEditingProduct.category : '';
    catField.append(catLabel, catInput);

    // Price & Old Price
    const priceRow = createElement('div', 'row');
    const priceField = createElement('div', 'form-field');
    priceField.style.flex = '1';
    const priceLabel = createElement('label', 'form-field__label', 'Price ($) *');
    const priceInput = createElement('input', 'form-field__input');
    priceInput.type = 'number';
    priceInput.step = '0.01';
    priceInput.min = '0';
    priceInput.required = true;
    priceInput.value = isEdit && currentEditingProduct.price != null ? String(currentEditingProduct.price) : '';
    priceField.append(priceLabel, priceInput);

    const oldPriceField = createElement('div', 'form-field');
    oldPriceField.style.flex = '1';
    const oldPriceLabel = createElement('label', 'form-field__label', 'Old Price ($)');
    const oldPriceInput = createElement('input', 'form-field__input');
    oldPriceInput.type = 'number';
    oldPriceInput.step = '0.01';
    oldPriceInput.min = '0';
    oldPriceInput.value = isEdit && currentEditingProduct.old_price != null ? String(currentEditingProduct.old_price) : '';
    oldPriceField.append(oldPriceLabel, oldPriceInput);
    priceRow.append(priceField, oldPriceField);

    // Stock quantity
    const stockField = createElement('div', 'form-field');
    const stockLabel = createElement('label', 'form-field__label', 'Stock Quantity *');
    const stockInput = createElement('input', 'form-field__input');
    stockInput.type = 'number';
    stockInput.min = '0';
    stockInput.required = true;
    stockInput.value = isEdit && currentEditingProduct.stock_quantity != null ? String(currentEditingProduct.stock_quantity) : '10';
    stockField.append(stockLabel, stockInput);

    // Image selection (from admin device or external URL)
    const imgField = createElement('div', 'form-field');
    const imgLabel = createElement('label', 'form-field__label', 'Product Image');

    const fileInput = createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/png,image/jpeg,image/webp,image/gif,image/svg+xml';
    fileInput.style.display = 'none';

    const pickerRow = createElement('div', 'row admin-image-picker');
    const uploadBtn = createElement('button', 'button button--outline admin-image-picker__upload-btn', '📁 Choose from Device');
    uploadBtn.type = 'button';
    uploadBtn.addEventListener('click', () => fileInput.click());

    const imgInput = createElement('input', 'form-field__input admin-image-picker__url-input');
    imgInput.type = 'text';
    imgInput.placeholder = 'Or paste image URL (https://... or /uploads/...)';
    if (isEdit && currentEditingProduct.image) {
        imgInput.dataset.realUrl = currentEditingProduct.image;
        imgInput.value = currentEditingProduct.imageDisplayName || (currentEditingProduct.image.startsWith('/uploads/') ? currentEditingProduct.image.split('/').pop() : currentEditingProduct.image);
    } else {
        imgInput.value = '';
    }

    pickerRow.append(uploadBtn, imgInput);

    // Preview box
    const previewBox = createElement('div', 'admin-image-preview');
    const previewImg = createElement('img', 'admin-image-preview__img');
    previewImg.alt = 'Product preview';
    const previewPlaceholder = createElement('span', 'admin-image-preview__placeholder', 'No image selected');
    previewBox.append(previewImg, previewPlaceholder);

    previewImg.addEventListener('error', () => {
        previewImg.hidden = true;
        previewPlaceholder.textContent = 'Failed to load preview';
        previewPlaceholder.hidden = false;
    });

    const updatePreview = (src) => {
        const actual = imgInput.dataset.realUrl || src;
        if (actual) {
            previewImg.src = actual.startsWith('/') ? `${API_BASE_URL}${actual}` : actual;
            previewImg.hidden = false;
            previewPlaceholder.hidden = true;
        } else {
            previewImg.hidden = true;
            previewPlaceholder.textContent = 'No image selected';
            previewPlaceholder.hidden = false;
        }
    };
    updatePreview(imgInput.dataset.realUrl || imgInput.value.trim());

    const saveDraftState = () => {
        if (!isEdit || !currentEditingProduct) return;
        sessionStorage.setItem(
            EDITING_STORAGE_KEY,
            JSON.stringify({
                id: currentEditingProduct.id,
                title: titleInput.value,
                description: descInput.value,
                category: catInput.value,
                price: priceInput.value,
                old_price: oldPriceInput.value,
                stock_quantity: stockInput.value,
                image: imgInput.dataset.realUrl || imgInput.value.trim(),
                imageDisplayName: imgInput.dataset.realUrl ? imgInput.value.trim() : '',
            })
        );
    };

    [titleInput, descInput, catInput, priceInput, oldPriceInput, stockInput, imgInput].forEach((input) => {
        input.addEventListener('input', () => {
            if (input === imgInput) {
                delete imgInput.dataset.realUrl;
                updatePreview(imgInput.value.trim());
            }
            saveDraftState();
        });
    });

    fileInput.addEventListener('change', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        // Show instant local preview
        const localUrl = URL.createObjectURL(file);
        updatePreview(localUrl);

        uploadBtn.disabled = true;
        uploadBtn.textContent = '⏳ Uploading...';

        try {
            const res = await apiUploadImage(file);
            imgInput.value = file.name;
            imgInput.dataset.realUrl = res.image_url;
            updatePreview(res.image_url);
            if (isEdit && currentEditingProduct) {
                currentEditingProduct.image = res.image_url;
                currentEditingProduct.imageDisplayName = file.name;
                saveDraftState();
            }
            showBanner('Image uploaded from device', 'success');
        } catch (err) {
            showBanner(err.message, 'error');
            updatePreview(imgInput.value.trim());
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = '📁 Choose from Device';
        }
    });

    imgField.append(imgLabel, fileInput, pickerRow, previewBox);

    // Actions
    const actionsRow = createElement('div', 'row admin-form__actions');
    const submitBtn = createElement('button', 'button button--primary', isEdit ? 'Save Changes' : 'Create Product');
    submitBtn.type = 'submit';

    const cancelBtn = createElement('button', 'button button--outline', 'Cancel');
    cancelBtn.type = 'button';
    cancelBtn.addEventListener('click', () => {
        sessionStorage.removeItem(EDITING_STORAGE_KEY);
        currentEditingProduct = null;
        formCard.hidden = true;
        onCancel();
    });

    actionsRow.append(submitBtn, cancelBtn);

    form.append(titleField, descField, catField, priceRow, stockField, imgField, actionsRow);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        submitBtn.disabled = true;

        const payload = {
            title: titleInput.value.trim(),
            description: descInput.value.trim(),
            category: catInput.value.trim(),
            price: Number.parseFloat(priceInput.value),
            old_price: oldPriceInput.value.trim() ? Number.parseFloat(oldPriceInput.value) : null,
            stock_quantity: Number.parseInt(stockInput.value, 10),
            image: imgInput.dataset.realUrl || imgInput.value.trim() || null,
        };

        try {
            if (isEdit) {
                await apiRequest(`/products/${currentEditingProduct.id}`, {
                    method: 'PUT',
                    body: payload,
                });
                showBanner('Product updated successfully', 'success');
            } else {
                await apiRequest('/products', {
                    method: 'POST',
                    body: payload,
                });
                showBanner('Product created successfully', 'success');
            }
            sessionStorage.removeItem(EDITING_STORAGE_KEY);
            currentEditingProduct = null;
            formCard.hidden = true;
            onSaved();
        } catch (error) {
            showBanner(error.message, 'error');
            submitBtn.disabled = false;
        }
    });

    formCard.append(title, form);
    formCard.hidden = false;
    formCard.scrollIntoView({ behavior: 'smooth' });
}

function confirmProductDeletion(productTitle) {
    return new Promise((resolve) => {
        const overlay = createElement('div', 'modal-overlay');
        const dialog = createElement('div', 'modal-dialog card');

        const title = createElement('h3', 'modal-dialog__title', 'Delete Product');
        const message = createElement(
            'p',
            'modal-dialog__message',
            "This product may currently be in a customer's shopping cart. Deleting this product will make the purchase impossible."
        );

        const actions = createElement('div', 'modal-dialog__actions');

        const cancelBtn = createElement('button', 'button button--outline', 'Cancel');
        cancelBtn.type = 'button';

        const continueBtn = createElement('button', 'button button--danger', 'Continue');
        continueBtn.type = 'button';

        const cleanup = (confirmed) => {
            overlay.remove();
            document.removeEventListener('keydown', onKeyDown);
            resolve(confirmed);
        };

        const onKeyDown = (e) => {
            if (e.key === 'Escape') cleanup(false);
        };

        cancelBtn.addEventListener('click', () => cleanup(false));
        continueBtn.addEventListener('click', () => cleanup(true));
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) cleanup(false);
        });

        document.addEventListener('keydown', onKeyDown);

        actions.append(cancelBtn, continueBtn);
        dialog.append(title, message, actions);
        overlay.append(dialog);
        document.body.append(overlay);

        continueBtn.focus();
    });
}

async function deleteProduct(productId, productTitle, onDeleted) {
    const confirmed = await confirmProductDeletion(productTitle);
    if (!confirmed) {
        return;
    }
    try {
        await apiRequest(`/products/${productId}`, { method: 'DELETE' });
        showBanner('Product deleted successfully', 'success');
        onDeleted();
    } catch (error) {
        showBanner(error.message, 'error');
    }
}

async function loadProducts(productsContainer, formCard, onProductChanged, currentRole) {
    productsContainer.replaceChildren(createElement('div', 'state-message', 'Loading products...'));
    try {
        const products = await apiRequest('/products?limit=100');
        if (!products || products.length === 0) {
            productsContainer.replaceChildren(createElement('div', 'state-message', 'No products yet.'));
            return;
        }

        const tableWrapper = createElement('div', 'admin-table-wrapper card');
        const table = createElement('table', 'admin-table');
        const thead = createElement('thead');
        const headerRow = createElement('tr');
        ['ID', 'Image', 'Title', 'Category', 'Price', 'Stock', 'Actions'].forEach((h) =>
            headerRow.append(createElement('th', '', h))
        );
        thead.append(headerRow);

        const tbody = createElement('tbody');
        products.forEach((p) => {
            const tr = createElement('tr');

            // ID
            const tdId = createElement('td', 'admin-table__id', String(p.id));

            // Image
            const tdImg = createElement('td', 'admin-table__img-cell');
            const imgBox = createElement('div', 'admin-table__img-box');
            imgBox.append(createProductImage(p, 'admin-table__img'));
            tdImg.append(imgBox);

            // Title
            const tdTitle = createElement('td', 'admin-table__title');
            tdTitle.append(createLink('admin-table__link', detailsUrl(p.id), p.title));

            // Category
            const tdCat = createElement('td', '', p.category);

            // Price
            const tdPrice = createElement('td');
            const priceBox = createElement('div', 'price');
            priceBox.append(createElement('span', 'price__current', formatPrice(p.price)));
            if (p.old_price) {
                priceBox.append(createElement('span', 'price__old', formatPrice(p.old_price)));
            }
            tdPrice.append(priceBox);

            // Stock
            const tdStock = createElement('td', 'admin-table__stock');
            tdStock.textContent = String(p.stock_quantity);
            if (isSoldOut(p)) {
                tdStock.append(createElement('span', ' ', ''), createSoldOutBadge('badge--small'));
            }

            // Actions
            const tdActions = createElement('td');
            const actionsBox = createElement('div', 'admin-table__actions');
            const editBtn = createElement('button', 'button button--outline admin-table__action-btn', 'Edit');
            editBtn.type = 'button';
            editBtn.addEventListener('click', () => {
                currentEditingProduct = p;
                sessionStorage.setItem(
                    EDITING_STORAGE_KEY,
                    JSON.stringify({
                        id: p.id,
                        title: p.title,
                        description: p.description,
                        category: p.category,
                        price: p.price,
                        old_price: p.old_price,
                        stock_quantity: p.stock_quantity,
                        image: p.image || '',
                    })
                );
                buildProductForm(formCard, onProductChanged, () => {
                    sessionStorage.removeItem(EDITING_STORAGE_KEY);
                });
            });

            const delBtn = createElement('button', 'button button--danger admin-table__action-btn', 'Delete');
            delBtn.type = 'button';
            if (currentRole === ROLE.MANAGER) {
                delBtn.disabled = true;
                delBtn.title = 'Only administrators can delete products (RBAC)';
                delBtn.style.opacity = '0.35';
                delBtn.style.cursor = 'not-allowed';
            } else {
                delBtn.addEventListener('click', () => deleteProduct(p.id, p.title, onProductChanged));
            }

            actionsBox.append(editBtn, delBtn);
            tdActions.append(actionsBox);

            tr.append(tdId, tdImg, tdTitle, tdCat, tdPrice, tdStock, tdActions);
            tbody.append(tr);
        });

        table.append(thead, tbody);
        tableWrapper.append(table);
        productsContainer.replaceChildren(tableWrapper);

        const rawEditing = sessionStorage.getItem(EDITING_STORAGE_KEY);
        if (rawEditing) {
            try {
                const draft = JSON.parse(rawEditing);
                const foundProduct = products.find((prod) => prod.id === draft.id);
                if (foundProduct) {
                    currentEditingProduct = {
                        ...foundProduct,
                        ...(draft.title !== undefined ? { title: draft.title } : {}),
                        ...(draft.description !== undefined ? { description: draft.description } : {}),
                        ...(draft.category !== undefined ? { category: draft.category } : {}),
                        ...(draft.price !== undefined ? { price: draft.price } : {}),
                        ...(draft.old_price !== undefined ? { old_price: draft.old_price } : {}),
                        ...(draft.stock_quantity !== undefined ? { stock_quantity: draft.stock_quantity } : {}),
                        ...(draft.image !== undefined ? { image: draft.image } : {}),
                        ...(draft.imageDisplayName !== undefined ? { imageDisplayName: draft.imageDisplayName } : {}),
                    };
                    buildProductForm(formCard, onProductChanged, () => {
                        sessionStorage.removeItem(EDITING_STORAGE_KEY);
                    });
                }
            } catch {
                sessionStorage.removeItem(EDITING_STORAGE_KEY);
            }
        }
    } catch (error) {
        if (handleAuthError(error)) return;
        productsContainer.replaceChildren(createElement('div', 'state-message state-message--error', error.message));
    }
}

// ----------------- MAIN ADMIN VIEW -----------------
function renderAdminArea(currentRole, currentUser) {
    const layout = createElement('div', 'admin__layout stack');

    // Tabs
    const tabs = createElement('div', 'admin__tabs');
    tabs.setAttribute('role', 'tablist');

    const tabDashboard = createElement('button', 'admin__tab admin__tab--active', 'Dashboard');
    const tabProducts = createElement('button', 'admin__tab', 'Products');
    const tabUsers = createElement('button', 'admin__tab', 'Users (RBAC)');
    
    const tabList = [tabDashboard, tabProducts];
    if (currentRole === ROLE.ADMIN) {
        tabList.push(tabUsers);
    }
    tabList.forEach((t) => {
        t.type = 'button';
        tabs.append(t);
    });

    // Content panels
    const panelDashboard = createElement('section', 'admin__panel stack');
    const statsGrid = createElement('div', 'admin-stats-grid');
    panelDashboard.append(createElement('h2', 'admin__section-title', 'Overview'), statsGrid);

    const panelProducts = createElement('section', 'admin__panel stack');
    panelProducts.hidden = true;
    const productsHeader = createElement('div', 'admin__header-bar');
    productsHeader.append(createElement('h2', 'admin__section-title', 'Manage Products'));
    const createBtn = createElement('button', 'button button--primary', '+ Create Product');
    createBtn.type = 'button';
    productsHeader.append(createBtn);

    const formCard = createElement('div', 'admin-form-card card');
    formCard.hidden = true;

    const productsList = createElement('div', 'admin__products-list');
    panelProducts.append(productsHeader, formCard, productsList);

    const panelUsers = createElement('section', 'admin__panel stack');
    panelUsers.hidden = true;
    const usersList = createElement('div', 'admin__users-list');
    panelUsers.append(createElement('h2', 'admin__section-title', 'Registered Users & Access Control'), usersList);

    const refreshAll = () => {
        loadDashboardStats(statsGrid);
        loadProducts(productsList, formCard, refreshAll, currentRole);
        if (currentRole === ROLE.ADMIN) {
            loadUsers(usersList, currentUser, refreshAll);
        }
    };

    createBtn.addEventListener('click', () => {
        sessionStorage.removeItem(EDITING_STORAGE_KEY);
        currentEditingProduct = null;
        buildProductForm(formCard, refreshAll, () => {});
    });

    const setTab = (tabName, updateHash = true) => {
        [tabDashboard, tabProducts, tabUsers].forEach((t) => t.classList.remove('admin__tab--active'));
        [panelDashboard, panelProducts, panelUsers].forEach((p) => (p.hidden = true));

        if (tabName === 'products') {
            tabProducts.classList.add('admin__tab--active');
            panelProducts.hidden = false;
            if (updateHash) window.location.hash = 'products';
        } else if (tabName === 'users' && currentRole === ROLE.ADMIN) {
            tabUsers.classList.add('admin__tab--active');
            panelUsers.hidden = false;
            if (updateHash) window.location.hash = 'users';
        } else {
            tabDashboard.classList.add('admin__tab--active');
            panelDashboard.hidden = false;
            if (updateHash) window.location.hash = 'dashboard';
        }
    };

    tabDashboard.addEventListener('click', () => setTab('dashboard'));
    tabProducts.addEventListener('click', () => setTab('products'));
    if (currentRole === ROLE.ADMIN) {
        tabUsers.addEventListener('click', () => setTab('users'));
    }

    const panelsToAppend = [tabs, panelDashboard, panelProducts];
    if (currentRole === ROLE.ADMIN) {
        panelsToAppend.push(panelUsers);
    }
    layout.append(...panelsToAppend);
    container.replaceChildren(layout);

    const initialHash = (window.location.hash || '').replace('#', '');
    if (initialHash === 'products' || (initialHash === 'users' && currentRole === ROLE.ADMIN)) {
        setTab(initialHash, false);
    } else {
        setTab('dashboard', false);
    }

    window.addEventListener('hashchange', () => {
        const hash = (window.location.hash || '').replace('#', '');
        setTab(hash || 'dashboard', false);
    });

    refreshAll();
}

async function init() {
    initHeader();
    const { role, user } = await getAuthState();

    if (role !== ROLE.ADMIN && role !== ROLE.MANAGER) {
        queueBanner('You must be signed in as an administrator or manager to view this area.', 'error');
        window.location.replace('index.html');
        return;
    }

    renderAdminArea(role, user);
}

init();
