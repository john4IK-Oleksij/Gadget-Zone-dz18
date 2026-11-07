## Task

Add a basic automated integration test suite for the existing FastAPI project `Gadget-Zone-dz18`.

The goal is to verify the main business flows from `mission.md` and protect the existing authentication, authorization, product and cart behavior from regressions.

## Requirements

Use the project's existing architecture, dependencies and database setup where practical. Do not introduce unnecessary libraries or redesign the application.

Create a `tests/` structure appropriate for FastAPI integration tests.

The tests should cover these main flows:

### Authentication

1. Register a new user.
   - Expected status: `201`.
   - Verify the response contains `id`, `email`, and `is_admin`.
   - Do not expose `password_hash`.

2. Login with valid credentials.
   - Expected status: `200`.
   - Verify `access_token` and `token_type`.

3. Access `/users/me` without authentication.
   - Expected status: `401`.

4. Access `/users/me` with a valid user token.
   - Expected status: `200`.
   - Verify the returned user belongs to the authenticated account.

### Authorization

5. A regular authenticated user attempts to create a product.
   - Expected status: `403`.

6. An admin creates a product.
   - Expected status: `201`.
   - Verify the returned product has an auto-generated integer `id`.

7. A regular user attempts to access an admin-only endpoint such as `/admin/users`.
   - Expected status: `403`.

8. An admin accesses `/admin/users`.
   - Expected status: `200`.
   - Verify user data is returned without password hashes.

9. An admin accesses `/admin/stats`.
   - Expected status: `200`.
   - Verify `users_count` and `products_count` are present and are integers.

### Products

10. Guest can retrieve the product list.
    - Expected status: `200`.

11. Guest can retrieve an existing product by ID.
    - Expected status: `200`.

12. Admin can update an existing product.
    - Expected status: `200`.
    - Verify the product ID cannot be changed through the update request.

13. Admin can delete an existing product.
    - Expected status: `204`.

### Cart

14. Authenticated user can add a product to their own cart.
    - Expected status: `201`.

15. Authenticated user can retrieve their own cart.
    - Expected status: `200`.
    - Verify the expected product and quantity are returned.

16. Authenticated user can change cart item quantity.
    - Expected status: `200`.
    - Verify the new quantity.

17. Authenticated user can remove a cart item.
    - Expected status: `204`.

18. Verify cart isolation.
    - Create two different users.
    - Add a product to User 1's cart.
    - Authenticate as User 2.
    - Verify User 2 does not see User 1's cart item.
    - Verify User 2 cannot modify or delete User 1's cart item.

### Product stock

19. Create/update a product with `stock_quantity = 0`.
    - The product must remain accessible through the product catalog.
    - Verify `stock_quantity` is `0`.
    - Verify it is not automatically removed from the database or cart.

## Important constraints

- Tests must use isolated test data and must not depend on the manually created development admin account.
- Do not modify production business logic merely to make tests pass.
- Do not weaken authentication or authorization for testing.
- Do not add `ondelete="CASCADE"` or change product/cart deletion behavior just for the tests.
- Do not introduce an online-users/session tracking mechanism.
- Do not add checkout, payments, orders or other features outside the current `mission.md`.
- Reuse the existing Pydantic schemas, services, dependencies and API routes.
- Keep tests readable and focused on observable HTTP behavior.
- Avoid excessive mocking; these should be real integration tests against a test database.
- If the current MySQL setup makes isolated automated tests impractical, first inspect the existing configuration and explain the minimal required testing setup instead of silently changing the production database configuration.

## Expected result

After implementation, provide:

1. The created/changed test files.
2. The exact command to run the test suite.
3. A short summary of what each test group verifies.
4. The test result.
5. Any remaining issue that prevents the integration suite from being considered complete.

Do not rewrite unrelated application code.