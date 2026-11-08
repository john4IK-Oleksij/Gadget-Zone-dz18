# Gadget Zone — Checklist ітерацій Frontend

Позначай `[x]` тільки після фактичного виконання та перевірки ітерації.

## Iteration 1 — Базова структура

- [x] Створено frontend структуру.
- [x] Створено базові HTML сторінки.
- [x] Підключено CSS.
- [x] Підключено JS modules.
- [x] Налаштовано API base URL.
- [x] Перевірено відкриття сторінок без console errors.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 2 — Design system

- [x] Додано палітру Cream + Dark Green + Graphite + Mustard Gold (60/30/10).
- [x] Додано базові typography / spacing rules.
- [x] Додано BEM naming.
- [x] Створено базові reusable UI classes.
- [ ] Перевірено desktop та mobile основу.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 3 — Shared Header

- [x] Реалізовано спільний header.
- [x] Logo → Home.
- [x] Desktop navigation.
- [x] Search field UI без fake search logic.
- [x] Account control.
- [ ] User cart control.
- [ ] Admin cart hidden.
- [x] Burger menu до `767px`.
- [x] Header працює на всіх сторінках.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 4 — Shop / Product Cards

- [x] Отримання товарів через `GET /products`.
- [x] Product grid.
- [x] Image.
- [x] Placeholder-фон, якщо image відсутнє або не завантажилось.
- [x] Title.
- [x] Title клікабельний → details.
- [x] Current price.
- [x] Old price gray + crossed out.
- [x] SOLD OUT для `stock_quantity = 0`.
- [ ] Hover image background.
- [ ] Eye action.
- [ ] Cart action.
- [ ] Guest → login.
- [ ] User → add to cart.
- [ ] Admin → cart action hidden.
- [x] Без ratings.
- [x] Без fake badges.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 5 — Details

- [x] `details.html?id=...`.
- [x] Product loading через backend.
- [x] Breadcrumb.
- [x] Image.
- [x] Title.
- [x] ID / SKU.
- [x] Availability.
- [x] Category.
- [x] Price.
- [ ] Old price.
- [x] Quantity control.
- [x] Add to Cart.
- [ ] Stock 0 → unavailable.
- [ ] Guest → login.
- [ ] User → backend cart.
- [x] Back / Return navigation.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 6 — Login / Sign Up

- [x] `login.html`.
- [x] Sign In.
- [x] Sign Up.
- [x] Перемикання Sign In / Sign Up.
- [x] Email.
- [x] Password.
- [x] Show/hide password.
- [x] Login API.
- [x] Register API.
- [x] JWT storage.
- [x] `GET /users/me`.
- [x] Визначення ролі.
- [x] Без Forgot Password.
- [x] Без Google/Apple login.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 7 — Logout / Auth UI

- [x] Account menu.
- [x] Logout.
- [x] JWT очищається.
- [x] Auth state очищається.
- [x] Redirect на Home.
- [x] Green success banner.
- [x] Login success banner.
- [x] User/Admin UI коректно оновлюється після login/logout.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 8 — Cart

- [x] `cart.html`.
- [x] `GET /cart`.
- [x] Product image.
- [x] Clickable title.
- [x] Current price.
- [x] Old price.
- [x] Quantity.
- [x] Subtotal.
- [x] Total.
- [x] Remove.
- [x] Quantity update.
- [x] Return to Shop.
- [x] Stock 0 показується як unavailable.
- [x] User бачить тільки власний cart.
- [x] Admin не має cart.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 9 — Mini-cart

- [x] Mini-cart для User.
- [x] Desktop hover.
- [x] Desktop click.
- [x] Mobile click/touch.
- [x] Image.
- [x] Title.
- [x] Quantity.
- [x] Price.
- [x] Remove.
- [x] Subtotal.
- [x] View Cart.
- [x] Дані синхронізовані з backend.
- [x] Admin mini-cart hidden.
- [x] Guest cart → login.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 10 — Admin

- [x] Admin page.
- [x] Role protection.
- [x] Dashboard.
- [x] Users count.
- [x] Products count.
- [x] Users list.
- [x] Product list.
- [x] Create product.
- [x] Edit product.
- [x] Change stock.
- [x] Delete product.
- [x] Product ID read-only.
- [x] Admin cart hidden.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 11 — Responsive / Mobile

- [x] Breakpoint `767px`.
- [x] Burger menu.
- [x] Product grid.
- [x] Details layout.
- [x] Cart layout.
- [x] Login layout.
- [x] Admin layout.
- [x] Touch controls.
- [x] Hover-only actions мають mobile alternative.

**Після завершення — STOP і чекати підтвердження.**

---

## Iteration 12 — Загальна перевірка

- [ ] Guest flow.
- [ ] Register.
- [ ] Login.
- [ ] User flow.
- [ ] User cart isolation.
- [ ] Mini-cart.
- [ ] Logout.
- [ ] Admin login.
- [ ] Admin product CRUD.
- [ ] Admin users.
- [ ] Admin stats.
- [ ] Admin has no cart.
- [ ] Stock 0.
- [ ] Details.
- [ ] Responsive.
- [ ] Console errors перевірені.
- [ ] Не залишилось fake / unsupported functionality.

**Frontend готовий після завершення цієї ітерації.**
