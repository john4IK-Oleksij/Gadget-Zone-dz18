import { initHeader } from './header.js';
import { apiRequest } from './api.js';
import { setToken } from './auth.js';
import { getAuthState, resetAuthState, ROLE } from './state.js';
import { queueBanner } from './banner.js';
import { createElement, createEyeIcon, createEyeOffIcon } from './ui.js';

const container = document.getElementById('auth');

const MODE = Object.freeze({ SIGN_IN: 'sign-in', SIGN_UP: 'sign-up' });

// Only same-site pages are allowed as a return target (no open redirects).
const ALLOWED_NEXT = /^(index|details|cart|admin)\.html(\?[\w=&%.-]*)?$/;

function getReturnPage() {
    const next = new URLSearchParams(window.location.search).get('next');
    return next && ALLOWED_NEXT.test(next) ? next : 'index.html';
}

function buildField(id, labelText, input) {
    const field = createElement('div', 'form-field');
    const label = createElement('label', 'form-field__label', labelText);
    label.htmlFor = id;
    field.append(label, input);
    return field;
}

function buildPasswordField(passwordInput) {
    const field = buildField('auth-password', 'Password', passwordInput);

    const wrapper = createElement('div', 'password-field');
    const toggle = createElement('button', 'password-field__toggle');
    toggle.type = 'button';

    const setVisible = (visible) => {
        passwordInput.type = visible ? 'text' : 'password';
        toggle.setAttribute('aria-label', visible ? 'Hide password' : 'Show password');
        toggle.setAttribute('aria-pressed', String(visible));
        toggle.replaceChildren(visible ? createEyeOffIcon() : createEyeIcon());
    };
    toggle.addEventListener('click', () => setVisible(passwordInput.type === 'password'));
    setVisible(false);

    wrapper.append(passwordInput, toggle);
    field.append(wrapper);
    return field;
}

function buildAuthCard() {
    let mode = window.location.hash === '#sign-up' ? MODE.SIGN_UP : MODE.SIGN_IN;

    const card = createElement('section', 'auth__card card');

    const tabs = createElement('div', 'auth__tabs');
    tabs.setAttribute('role', 'tablist');
    const signInTab = createElement('button', 'auth__tab', 'Sign In');
    const signUpTab = createElement('button', 'auth__tab', 'Sign Up');
    [signInTab, signUpTab].forEach((tab) => {
        tab.type = 'button';
        tab.setAttribute('role', 'tab');
    });
    tabs.append(signInTab, signUpTab);

    const form = createElement('form', 'auth__form stack');

    const emailInput = createElement('input', 'form-field__input');
    emailInput.id = 'auth-email';
    emailInput.type = 'email';
    emailInput.required = true;
    emailInput.autocomplete = 'email';

    const passwordInput = createElement('input', 'form-field__input');
    passwordInput.id = 'auth-password';
    passwordInput.type = 'password';
    passwordInput.required = true;

    const message = createElement('p', 'auth__message');
    message.setAttribute('role', 'alert');
    message.hidden = true;

    const submit = createElement('button', 'button button--primary auth__submit');
    submit.type = 'submit';

    form.append(
        buildField('auth-email', 'Email', emailInput),
        buildPasswordField(passwordInput),
        message,
        submit,
    );
    card.append(tabs, form);

    const showError = (text) => {
        message.textContent = text;
        message.hidden = false;
    };

    const applyMode = (nextMode) => {
        mode = nextMode;
        const isSignIn = mode === MODE.SIGN_IN;
        signInTab.classList.toggle('auth__tab--active', isSignIn);
        signUpTab.classList.toggle('auth__tab--active', !isSignIn);
        signInTab.setAttribute('aria-selected', String(isSignIn));
        signUpTab.setAttribute('aria-selected', String(!isSignIn));
        passwordInput.autocomplete = isSignIn ? 'current-password' : 'new-password';
        submit.textContent = isSignIn ? 'Sign In' : 'Sign Up';
        message.hidden = true;
        document.title = `${isSignIn ? 'Sign In' : 'Sign Up'} | Gadget Zone`;
    };
    signInTab.addEventListener('click', () => applyMode(MODE.SIGN_IN));
    signUpTab.addEventListener('click', () => applyMode(MODE.SIGN_UP));

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        message.hidden = true;
        submit.disabled = true;

        const email = emailInput.value.trim();
        const password = passwordInput.value;

        try {
            if (mode === MODE.SIGN_UP) {
                await apiRequest('/auth/register', {
                    method: 'POST',
                    body: { email, password },
                    auth: false,
                });
            }
            // The login endpoint expects form fields named "username" and "password".
            const token = await apiRequest('/auth/login', {
                method: 'POST',
                form: { username: email, password },
                auth: false,
            });
            setToken(token.access_token, token.refresh_token);
            resetAuthState();
            queueBanner(mode === MODE.SIGN_UP ? 'Account created. Welcome!' : 'You are logged in.', 'success');
            window.location.href = getReturnPage();
        } catch (error) {
            showError(error.message);
            submit.disabled = false;
        }
    });

    applyMode(mode);
    return card;
}

async function init() {
    initHeader();
    const { role } = await getAuthState();
    if (role !== ROLE.GUEST) {
        window.location.replace('index.html');
        return;
    }
    container.replaceChildren(buildAuthCard());
}

init();
