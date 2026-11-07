import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.user import User


async def create_user_token(client: AsyncClient, email: str, password: str) -> str:
    """Helper to create a regular user and return their token."""
    await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )

    login_response = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    return login_response.json()["access_token"]


async def create_admin_token(client: AsyncClient) -> str:
    """Helper to create an admin user and return their token."""
    email = f"admin{id(client)}@example.com"
    password = "adminpass"

    register_response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    admin_id = register_response.json()["id"]

    session = client.app.dependency_overrides[
        __import__("app.db.session", fromlist=["get_db"]).get_db
    ]()
    stmt = update(User).where(User.id == admin_id).values(is_admin=True)
    await session.execute(stmt)
    await session.commit()

    login_response = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    return login_response.json()["access_token"]


async def create_test_product(client: AsyncClient, admin_token: str) -> int:
    """Helper to create a test product and return its ID."""
    response = await client.post(
        "/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Test Product",
            "description": "A product for cart testing",
            "price": 99.99,
            "category": "Electronics",
            "stock_quantity": 100,
        },
    )
    return response.json()["id"]


class TestCart:
    """Test cart operations and cart isolation."""

    @pytest.mark.asyncio
    async def test_authenticated_user_add_to_cart(self, client: AsyncClient):
        """Test 14: Authenticated user can add a product to their own cart.
        - Expected status: 201
        """
        admin_token = await create_admin_token(client)
        product_id = await create_test_product(client, admin_token)

        user_token = await create_user_token(
            client,
            "cartuser@example.com",
            "password123",
        )

        response = await client.post(
            "/cart/items",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "product_id": product_id,
                "quantity": 2,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["product_id"] == product_id
        assert data["quantity"] == 2

    @pytest.mark.asyncio
    async def test_authenticated_user_retrieve_cart(self, client: AsyncClient):
        """Test 15: Authenticated user can retrieve their own cart.
        - Expected status: 200
        - Verify the expected product and quantity are returned
        """
        admin_token = await create_admin_token(client)
        product_id = await create_test_product(client, admin_token)

        user_token = await create_user_token(
            client,
            "cartuser2@example.com",
            "password123",
        )

        await client.post(
            "/cart/items",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "product_id": product_id,
                "quantity": 3,
            },
        )

        response = await client.get(
            "/cart",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total_items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == product_id
        assert data["items"][0]["quantity"] == 3

    @pytest.mark.asyncio
    async def test_user_change_cart_item_quantity(self, client: AsyncClient):
        """Test 16: Authenticated user can change cart item quantity.
        - Expected status: 200
        - Verify the new quantity
        """
        admin_token = await create_admin_token(client)
        product_id = await create_test_product(client, admin_token)

        user_token = await create_user_token(
            client,
            "cartuser3@example.com",
            "password123",
        )

        await client.post(
            "/cart/items",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "product_id": product_id,
                "quantity": 1,
            },
        )

        response = await client.patch(
            f"/cart/items/{product_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"quantity": 5},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["quantity"] == 5

    @pytest.mark.asyncio
    async def test_user_remove_cart_item(self, client: AsyncClient):
        """Test 17: Authenticated user can remove a cart item.
        - Expected status: 204
        """
        admin_token = await create_admin_token(client)
        product_id = await create_test_product(client, admin_token)

        user_token = await create_user_token(
            client,
            "cartuser4@example.com",
            "password123",
        )

        await client.post(
            "/cart/items",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "product_id": product_id,
                "quantity": 2,
            },
        )

        response = await client.delete(
            f"/cart/items/{product_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 204

        cart_response = await client.get(
            "/cart",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert len(cart_response.json()["items"]) == 0

    @pytest.mark.asyncio
    async def test_cart_isolation_between_users(self, client: AsyncClient):
        """Test 18: Verify cart isolation between users.
        - Create two different users
        - Add a product to User 1's cart
        - Authenticate as User 2
        - Verify User 2 does not see User 1's cart item
        - Verify User 2 cannot modify or delete User 1's cart item
        """
        admin_token = await create_admin_token(client)
        product_id = await create_test_product(client, admin_token)

        user1_token = await create_user_token(
            client,
            "user1@example.com",
            "password123",
        )
        user2_token = await create_user_token(
            client,
            "user2@example.com",
            "password123",
        )

        await client.post(
            "/cart/items",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "product_id": product_id,
                "quantity": 3,
            },
        )

        user2_cart = await client.get(
            "/cart",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert len(user2_cart.json()["items"]) == 0

        update_response = await client.patch(
            f"/cart/items/{product_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
            json={"quantity": 1},
        )
        assert update_response.status_code != 200

        delete_response = await client.delete(
            f"/cart/items/{product_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert delete_response.status_code != 204

        user1_cart = await client.get(
            "/cart",
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        assert len(user1_cart.json()["items"]) == 1
        assert user1_cart.json()["items"][0]["quantity"] == 3
