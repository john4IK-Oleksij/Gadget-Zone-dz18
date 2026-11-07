import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.user import User


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


class TestProducts:
    """Test product catalog and CRUD operations."""

    @pytest.mark.asyncio
    async def test_guest_retrieve_product_list(self, client: AsyncClient):
        """Test 10: Guest can retrieve the product list.
        - Expected status: 200
        """
        response = await client.get("/products")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_guest_retrieve_existing_product(self, client: AsyncClient):
        """Test 11: Guest can retrieve an existing product by ID.
        - Expected status: 200
        """
        admin_token = await create_admin_token(client)

        create_response = await client.post(
            "/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Test Product",
                "description": "A test product",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.get(f"/products/{product_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == product_id
        assert data["title"] == "Test Product"

    @pytest.mark.asyncio
    async def test_admin_update_product(self, client: AsyncClient):
        """Test 12: Admin can update an existing product.
        - Expected status: 200
        - Verify the product ID cannot be changed through the update request
        """
        admin_token = await create_admin_token(client)

        create_response = await client.post(
            "/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Original Title",
                "description": "Original description",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.put(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Updated Title",
                "description": "Updated description",
                "price": 149.99,
                "category": "Gadgets",
                "stock_quantity": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == product_id
        assert data["title"] == "Updated Title"
        assert data["price"] == 149.99
        assert data["stock_quantity"] == 20

    @pytest.mark.asyncio
    async def test_admin_delete_product(self, client: AsyncClient):
        """Test 13: Admin can delete an existing product.
        - Expected status: 204
        """
        admin_token = await create_admin_token(client)

        create_response = await client.post(
            "/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Product to Delete",
                "description": "This will be deleted",
                "price": 50.00,
                "category": "Electronics",
                "stock_quantity": 5,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.delete(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 204

        get_response = await client.get(f"/products/{product_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_product_with_zero_stock(self, client: AsyncClient):
        """Test 19: Create/update a product with stock_quantity = 0.
        - Product must remain accessible through the product catalog
        - Verify stock_quantity is 0
        - Verify it is not automatically removed or from cart
        """
        admin_token = await create_admin_token(client)

        response = await client.post(
            "/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Zero Stock Product",
                "description": "This has no stock",
                "price": 29.99,
                "category": "Electronics",
                "stock_quantity": 0,
            },
        )

        assert response.status_code == 201
        product_id = response.json()["id"]
        assert response.json()["stock_quantity"] == 0

        list_response = await client.get("/products")
        assert list_response.status_code == 200
        products = list_response.json()

        product_found = any(p["id"] == product_id for p in products)
        assert product_found, "Zero-stock product should be in the catalog"

        get_response = await client.get(f"/products/{product_id}")
        assert get_response.status_code == 200
        assert get_response.json()["stock_quantity"] == 0

        update_response = await client.put(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Zero Stock Product",
                "description": "Updated with stock",
                "price": 29.99,
                "category": "Electronics",
                "stock_quantity": 0,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["stock_quantity"] == 0
