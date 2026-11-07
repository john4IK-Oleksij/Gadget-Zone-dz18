import pytest
from httpx import AsyncClient


class TestAuthentication:
    """Test authentication flows: register, login, and token validation."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient):
        """Test 1: Register a new user.
        - Expected status: 201
        - Verify response contains id, email, is_admin
        - Verify password_hash is not exposed
        """
        response = await client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["email"] == "testuser@example.com"
        assert "is_admin" in data
        assert data["is_admin"] is False
        assert "password_hash" not in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registering with duplicate email returns 409."""
        email = "duplicate@example.com"
        password = "password123"

        await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )

        response = await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, client: AsyncClient):
        """Test 2: Login with valid credentials.
        - Expected status: 200
        - Verify access_token and token_type are present
        """
        email = "loginuser@example.com"
        password = "securepassword123"

        await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )

        response = await client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials returns 401."""
        email = "testuser@example.com"

        await client.post(
            "/auth/register",
            json={"email": email, "password": "correctpassword"},
        )

        response = await client.post(
            "/auth/login",
            data={
                "username": email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_access_me_without_auth(self, client: AsyncClient):
        """Test 3: Access /users/me without authentication.
        - Expected status: 401
        """
        response = await client.get("/users/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_access_me_with_valid_token(self, client: AsyncClient):
        """Test 4: Access /users/me with a valid user token.
        - Expected status: 200
        - Verify the returned user belongs to the authenticated account
        """
        email = "authuser@example.com"
        password = "securepassword123"

        register_response = await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )
        user_id = register_response.json()["id"]

        login_response = await client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
            },
        )
        token = login_response.json()["access_token"]

        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user_id
        assert data["email"] == email
        assert data["is_admin"] is False
        assert "password_hash" not in data
