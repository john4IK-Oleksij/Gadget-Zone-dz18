# Gadget Zone — Specifications

## 1. Project scope

Build a backend for an online gadget shop using Python and FastAPI.

The implementation should be intentionally practical and small enough to understand. Do not add orders, checkout, payments, reservations, stock locking, or other business logic unless it becomes necessary later.

## 2. Core entities

The initial domain consists of:

- User
- Product
- Cart
- CartItem

Authentication-related data may include refresh-token/session data depending on the chosen implementation from the reference architecture.

## 3. Product

The product must have an immutable ID.

The product must contain a stock quantity:

- `stock_quantity > 0` → available.
- `stock_quantity = 0` → product remains in the catalog but is temporarily unavailable.

Admins can change the stock quantity.

A product can also be deleted by an admin. Deletion is a separate operation from setting stock to zero.

Exact product fields beyond the confirmed requirements will be defined when the product model/schema is implemented.

## 4. Product API

Public product functionality:

- list products;
- open a product by ID;
- return appropriate response when a product does not exist.

Admin product functionality:

- create product;
- update product;
- change stock quantity;
- delete product.

Update requests must not allow changing the product ID.

Authorization must be checked separately from authentication:

- unauthenticated request → authentication requirement;
- authenticated non-admin request to an admin endpoint → `403 Forbidden`;
- admin request → allowed.

## 5. Authentication

Use the authentication approach from the current learning material/reference architecture where appropriate.

Required flows:

- registration;
- login;
- authenticated user identification;
- protected endpoints;
- admin authorization.

The authentication implementation should keep authentication and authorization as separate concepts.

## 6. Cart

A cart belongs to an authenticated user.

A user can:

- view their own cart;
- add a product;
- change the quantity of a cart item;
- remove a cart item.

A user must not be able to access or modify another user's cart.

Recommended simple rule:

- adding the same product again should increase the existing CartItem quantity instead of creating duplicate CartItem rows.

Quantity must be a positive integer.

A product with `stock_quantity = 0` may remain in an existing cart. It must be presented as temporarily unavailable.

Do not introduce reservation logic.

## 7. Error behavior

The API should use clear HTTP status codes and consistent error responses.

At minimum, handle:

- invalid request data;
- missing authentication;
- insufficient permissions;
- missing product;
- invalid cart quantity;
- missing cart item;
- invalid credentials / login failure.

Use centralized exception/response patterns where they improve consistency.

## 8. Architecture

Keep the application separated into understandable layers.

Expected responsibility flow:

- routers — HTTP endpoints;
- dependencies — reusable request-level dependencies such as current user/admin checks;
- schemas — request/response validation;
- services — business operations;
- models — database entities;
- database layer — sessions/connection handling;
- core — configuration, security, exceptions and shared infrastructure.

The exact final structure can be adjusted while implementing the project.

## 9. Security

Use secure password hashing.

Keep secrets and database credentials in environment configuration rather than source code.

Protect authenticated endpoints.

Protect admin endpoints with role authorization.

Do not trust a user ID supplied by the client when determining ownership of a cart. Ownership should come from the authenticated user context.

## 10. Database

Use MySQL with SQLAlchemy.

Database relationships should support:

- user → cart;
- cart → cart items;
- product → cart items.

The behavior of foreign keys when a physically deleted product has existing CartItems must be selected explicitly during implementation. Do not silently assume cascade behavior.

## 11. Testing

Test the important access and business flows, including:

### Guest
- can list products;
- can view product details;
- cannot access protected cart endpoints;
- cannot access admin product endpoints.

### User
- can access their own cart;
- can add a product;
- can change quantity;
- can remove a cart item;
- cannot perform admin product operations.

### Admin
- can create a product;
- can update product data except ID;
- can change stock;
- can set stock to `0`;
- can delete a product.

### Stock
- product with stock `0` remains visible;
- product with stock `0` is marked temporarily unavailable in the cart.

## 12. Implementation rule

Implement in small phases.

Do not build the entire application in one giant step.

For each phase:

1. implement the relevant files;
2. run the application;
3. test the relevant endpoints;
4. explain the request/data flow;
5. only then move to the next phase.

The ZIP/reference project should be treated as a reusable architecture template: copy the useful pattern, understand why it exists, then adapt it to Gadget Zone.
