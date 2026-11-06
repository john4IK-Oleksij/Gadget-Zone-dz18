# Gadget Zone — Mission

## Project

Gadget Zone is a practical FastAPI backend project for an online shop. The project is built as a learning project while applying the architecture and reusable patterns from the reference codebase and authentication presentations.

Repository:
https://github.com/john4IK-Oleksij/Gadget-Zone-dz18.git

## Confirmed business rules

### Roles

#### Guest
- Browse products.
- Open product details.
- Register / log in.
- Cannot use the cart.
- Cannot create, edit, or delete products.

#### Authenticated user
- Browse products.
- Open product details.
- View their own cart.
- Add products to their own cart.
- Change quantity of each cart item.
- Remove products from their own cart.
- Cannot create, edit, or delete products.

#### Admin
- Has all authenticated-user capabilities.
- Can create products.
- Can edit product fields except the product ID.
- Can change product stock quantity.
- Can delete products from the system.

### Product stock

- `stock_quantity = 0`
  → the product exists in the system but is temporarily unavailable.
- A product with stock `0` stays in the catalog.
- If such a product is already in a user's cart, the CartItem is not automatically removed.
- In the cart, an unavailable product should be shown as `Тимчасово недоступний`.

### Product deletion

- `DELETE product`
  → the product is removed from the system.
- Deleting a product is different from setting `stock_quantity` to `0`.
- The database behavior for existing CartItem records referencing a physically deleted product must be implemented deliberately during the DB/model phase.

## Access matrix

| Action | Guest | User | Admin |
|---|---:|---:|---:|
| Product list | Yes | Yes | Yes |
| Product details | Yes | Yes | Yes |
| Register | Yes | — | — |
| Login | Yes | — | — |
| View own cart | No | Yes | Yes |
| Add to own cart | No | Yes | Yes |
| Change cart quantity | No | Yes | Yes |
| Remove cart item | No | Yes | Yes |
| Create product | No | No | Yes |
| Edit product | No | No | Yes |
| Change stock | No | No | Yes |
| Delete product | No | No | Yes |

Product ID is immutable through update operations.

## Main learning goal

Build the project incrementally while understanding the request flow:

frontend/client → HTTP → router → dependencies/auth → service → DB → response → frontend/client

The project should reuse practical patterns rather than copy code blindly.

## Definition of done

- Working FastAPI application.
- MySQL database integration.
- Product catalog and details.
- Authentication.
- Authorization with user/admin roles.
- User-specific cart.
- Product stock quantity.
- Admin product CRUD.
- Correct handling of unavailable products.
- Clear project structure.
- Centralized configuration, exceptions, security, dependencies and services where appropriate.
- Basic integration testing of the main flows.
