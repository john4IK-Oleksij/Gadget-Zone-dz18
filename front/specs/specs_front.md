# Gadget Zone — Технічні специфікації Frontend

## 1. Структура

Рекомендована структура:

```text
front/
├── index.html
├── details.html
├── cart.html
├── login.html
├── admin.html
├── css/
│   ├── base.css
│   ├── layout.css
│   ├── components.css
│   └── responsive.css
├── js/
│   ├── api.js
│   ├── auth.js
│   ├── state.js
│   ├── header.js
│   ├── products.js
│   ├── details.js
│   ├── cart.js
│   ├── login.js
│   └── admin.js
└── assets/
```

Структуру можна трохи змінити, якщо відповідальності залишаються розділеними.

## 2. API base URL

Backend URL зберігати в одному місці.

Наприклад:

```js
const API_BASE_URL = 'http://127.0.0.1:8000';
```

Не дублювати URL у різних JS-файлах.

Frontend запускається через VS Code Live Server (`http://127.0.0.1:5500`). Цей origin дозволений у backend CORS (`cors_origins` у `app/core/config.py`).

## 3. Auth

JWT зберігати на frontend.

Protected request:

```text
Authorization: Bearer <token>
```

Auth state повинен централізовано визначати:

```text
Guest
User
Admin
```

Frontend role checks керують UI, але не є security boundary.

## 4. Product card

Дані:

```text
id
title
description
image
price
old_price
category
stock_quantity
```

`old_price`:
- сірий;
- `text-decoration: line-through`.

`stock_quantity === 0`:
- gray SOLD OUT badge;
- cart action disabled/hidden.

Hover:
- змінити background image area;
- показати Eye;
- показати Cart.

Eye і Title (обидва ведуть на details):

```text
details.html?id={id}
```

Image placeholder:
- якщо `image` порожнє/null або не завантажилось — показати placeholder-фон (клас `media-placeholder`), щоб розмір картки не стрибав;
- placeholder не є fake-даними, це лише візуальне заповнення.

## 5. Details

Отримати `id` з query string.

```text
details.html?id=15
```

Запит:

```text
GET /products/15
```

Quantity:
- default `1`;
- minimum `1`.

Add to Cart для User:

```text
POST /cart/items
```

Body:

```json
{
  "product_id": 15,
  "quantity": 1
}
```

## 6. Cart

Запит:

```text
GET /cart
```

Add:

```text
POST /cart/items
```

Update:

```text
PATCH /cart/items/{product_id}
```

Delete:

```text
DELETE /cart/items/{product_id}
```

Item subtotal:

```text
price × quantity
```

Total:

```text
sum(item subtotal)
```

Не створювати fake shipping/tax/discount logic.

## 7. Mini-cart

Mini-cart повинен використовувати ті самі cart data, що і `cart.html`.

Не створювати окремий fake cart state, який може розходитися з backend.

## 8. Login

```text
POST /auth/login
```

Після login:

```text
JWT
 ↓
GET /users/me
 ↓
визначити роль
 ↓
оновити shared UI
 ↓
redirect
```

Register:

```text
POST /auth/register
```

Не реалізовувати social auth.

## 9. Admin

Admin UI доступний тільки після визначення:

```text
is_admin === true
```

Stats:

```json
{
  "users_count": 30,
  "products_count": 42
}
```

Users:

```text
id
email
is_admin
```

Products:
- create;
- edit;
- stock;
- delete.

ID read-only.

## 10. Responsive

Основний breakpoint:

```css
@media (max-width: 767px)
```

Mobile:
- burger;
- адаптивна grid;
- touch-friendly controls;
- no dependency on hover.

## 11. Error handling

Показувати користувачу зрозуміле повідомлення.

Не показувати:
- stack trace;
- внутрішні exception details;
- password/hash.

Мати базові стани:

```text
Loading...
Empty...
Error...
Success...
```

## 12. Accessibility

Для interactive controls використовувати:

```text
button
a
input
select
```

Важливі controls повинні мати доступний текст / label.

Hover не повинен бути єдиним способом виконати важливу дію.

## 13. Browser verification

На кожній ітерації перевіряти тільки функціонал, який входить у поточну ітерацію.

Не переходити далі, якщо поточна ітерація має очевидну функціональну помилку.

Після завершення всієї реалізації виконати загальну інтеграційну перевірку основних потоків.
