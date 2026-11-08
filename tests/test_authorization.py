import pytest
from httpx import AsyncClient


async def register_user(
    client: AsyncClient,
    email: str,
    password: str,
    is_admin: bool = False,
) -> tuple[int, str]:
    """Helper to register a user and return (user_id, token)."""
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    user_id = response.json()["id"]

    if is_admin:
        from sqlalchemy import update
        from sqlalchemy.ext.asyncio import AsyncSession

        session = client.app.dependency_overrides[
            __import__("app.db.session", fromlist=["get_db"]).get_db
        ]()
        from app.models.user import User

        stmt = update(User).where(User.id == user_id).values(is_admin=True)
        await session.execute(stmt)
        await session.commit()

    login_response = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    token = login_response.json()["access_token"]

    return user_id, token


class TestAuthorization:
    """Test authorization flows: user vs admin permissions."""

    @pytest.mark.asyncio
    async def test_regular_user_create_product_forbidden(
        self,
        client: AsyncClient,
    ):
        """Test 5: A regular authenticated user attempts to create a product.
        - Expected status: 403
        """
        _, token = await register_user(
            client,
            "regularuser@example.com",
            "password123",
        )

        response = await client.post(
            "/products",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Test Product",
                "description": "A test product",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10,
            },
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_create_product_success(self, client: AsyncClient):
        """Test 6: An admin creates a product.
        - Expected status: 201
        - Verify the returned product has an auto-generated integer id
        """
        email = "adminuser@example.com"
        password = "adminpass123"

        register_response = await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )
        admin_id = register_response.json()["id"]

        from sqlalchemy import update
        from app.models.user import User

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
        token = login_response.json()["access_token"]

        response = await client.post(
            "/products",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Admin Product",
                "description": "Created by admin",
                "price": 199.99,
                "category": "Electronics",
                "stock_quantity": 50,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert isinstance(data["id"], int)
        assert data["title"] == "Admin Product"

    @pytest.mark.asyncio
    async def test_regular_user_access_admin_users_forbidden(
        self,
        client: AsyncClient,
    ):
        """Test 7: A regular user attempts to access /admin/users.
        - Expected status: 403
        """
        _, token = await register_user(
            client,
            "user@example.com",
            "password123",
        )

        response = await client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_access_users_success(self, client: AsyncClient):
        """Test 8: An admin accesses /admin/users.
        - Expected status: 200
        - Verify user data is returned without password hashes
        """
        email = "admin_users@example.com"
        password = "adminpass"

        register_response = await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )
        admin_id = register_response.json()["id"]

        from sqlalchemy import update
        from app.models.user import User

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
        token = login_response.json()["access_token"]

        response = await client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        for user in data:
            assert "id" in user
            assert "email" in user
            assert "is_admin" in user
            assert "password_hash" not in user
            assert "password" not in user

    @pytest.mark.asyncio
    async def test_admin_access_stats_success(self, client: AsyncClient):
        """Test 9: An admin accesses /admin/stats.
        - Expected status: 200
        - Verify users_count and products_count are present and are integers
        """
        email = "admin_stats@example.com"
        password = "adminpass"

        register_response = await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )
        admin_id = register_response.json()["id"]

        from sqlalchemy import update
        from app.models.user import User

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
        token = login_response.json()["access_token"]

        response = await client.get(
            "/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "users_count" in data
        assert "products_count" in data
        assert isinstance(data["users_count"], int)
        assert isinstance(data["products_count"], int)
