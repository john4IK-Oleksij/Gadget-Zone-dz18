from typing import Any
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TooManyRequestsError
from app.core.rate_limit import RateLimiter
from app.core.security import hash_token
from app.enums import Role
from app.models.refresh_token import RefreshToken
from app.models.user import User


async def _create_user_with_role(
    session: AsyncSession,
    email: str,
    role: Role,
    user_id: int | None = None,
) -> User:
    """Helper to seed a user with a specific role directly in the database."""
    from app.core.security import hash_password

    user = User(
        id=user_id,
        email=email,
        password_hash=await hash_password("Secret123!"),
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


class TestDZ19SecurityAndRBAC:
    """Comprehensive test suite for DZ-19 security and RBAC enhancements."""

    @pytest.mark.asyncio
    async def test_refresh_token_rotation_success(
        self, client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Test successful token rotation: old token is marked used, new token created in same family."""
        email = "rotate_user@example.com"
        password = "Password123!"

        # Register & Login
        await client.post("/auth/register", json={"email": email, "password": password})
        login_res = await client.post("/auth/login", data={"username": email, "password": password})
        assert login_res.status_code == 200
        first_refresh_cookie = login_res.cookies.get("refresh_token")
        assert first_refresh_cookie is not None

        # Perform Refresh using the cookie
        client.cookies.set("refresh_token", first_refresh_cookie)
        refresh_res = await client.post("/auth/refresh")
        assert refresh_res.status_code == 200
        data = refresh_res.json()
        assert "access_token" in data
        second_refresh_cookie = refresh_res.cookies.get("refresh_token")
        assert second_refresh_cookie is not None
        assert second_refresh_cookie != first_refresh_cookie

        # Verify in database
        first_hash = hash_token(first_refresh_cookie)
        second_hash = hash_token(second_refresh_cookie)

        stmt1 = select(RefreshToken).where(RefreshToken.token_hash == first_hash)
        old_token = (await test_session.execute(stmt1)).scalar_one_or_none()
        assert old_token is not None
        assert old_token.used_at is not None
        assert old_token.revoked_at is None

        stmt2 = select(RefreshToken).where(RefreshToken.token_hash == second_hash)
        new_token = (await test_session.execute(stmt2)).scalar_one_or_none()
        assert new_token is not None
        assert new_token.used_at is None
        assert new_token.revoked_at is None
        assert new_token.family_id == old_token.family_id

    @pytest.mark.asyncio
    async def test_token_reuse_detection_revokes_entire_family(
        self, client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Test Token Reuse Detection: re-using an already consumed token immediately revokes all tokens in family."""
        email = "reuse_victim@example.com"
        password = "Password123!"

        await client.post("/auth/register", json={"email": email, "password": password})
        login_res = await client.post("/auth/login", data={"username": email, "password": password})
        assert login_res.status_code == 200
        first_refresh = login_res.cookies.get("refresh_token")
        assert first_refresh is not None

        # Legitimate rotation
        client.cookies.set("refresh_token", first_refresh)
        rotate_res = await client.post("/auth/refresh")
        assert rotate_res.status_code == 200
        second_refresh = rotate_res.cookies.get("refresh_token")
        assert second_refresh is not None

        # Attacker tries to reuse the old first_refresh token!
        client.cookies.set("refresh_token", first_refresh)
        reuse_res = await client.post("/auth/refresh")
        assert reuse_res.status_code == 401
        assert "compromised" in reuse_res.json()["detail"].lower() or "invalid" in reuse_res.json()["detail"].lower()

        # Check database: entire family must be revoked
        first_hash = hash_token(first_refresh)
        old_token = (await test_session.execute(select(RefreshToken).where(RefreshToken.token_hash == first_hash))).scalar_one()
        family_tokens = (
            await test_session.execute(select(RefreshToken).where(RefreshToken.family_id == old_token.family_id))
        ).scalars().all()
        assert len(family_tokens) >= 2
        for t in family_tokens:
            assert t.revoked_at is not None

        # Now legitimate user trying to use second_refresh is also rejected because family is dead
        client.cookies.set("refresh_token", second_refresh)
        blocked_res = await client.post("/auth/refresh")
        assert blocked_res.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_single_device(
        self, client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Test POST /auth/logout revokes the session family and clears the cookie."""
        email = "logout_single@example.com"
        password = "Password123!"

        await client.post("/auth/register", json={"email": email, "password": password})
        login_res = await client.post("/auth/login", data={"username": email, "password": password})
        token = login_res.json()["access_token"]
        refresh_val = login_res.cookies.get("refresh_token")
        assert refresh_val is not None

        client.cookies.set("refresh_token", refresh_val)
        logout_res = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_res.status_code == 200

        # Token must be revoked in database
        thash = hash_token(refresh_val)
        db_token = (await test_session.execute(select(RefreshToken).where(RefreshToken.token_hash == thash))).scalar_one()
        assert db_token.revoked_at is not None

        # Refresh must now fail
        client.cookies.set("refresh_token", refresh_val)
        fail_res = await client.post("/auth/refresh")
        assert fail_res.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_all_devices(
        self, client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Test POST /auth/logout-all revokes all sessions across all devices for the user."""
        email = "multi_device@example.com"
        password = "Password123!"

        await client.post("/auth/register", json={"email": email, "password": password})

        # Device 1 login
        login1 = await client.post("/auth/login", data={"username": email, "password": password})
        token1 = login1.json()["access_token"]
        refresh1 = login1.cookies.get("refresh_token")
        assert refresh1 is not None

        # Device 2 login
        login2 = await client.post("/auth/login", data={"username": email, "password": password})
        refresh2 = login2.cookies.get("refresh_token")
        assert refresh2 is not None

        # Device 1 triggers logout-all
        logout_all_res = await client.post(
            "/auth/logout-all",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert logout_all_res.status_code == 200

        # Both tokens must now be revoked in MySQL
        thash1 = hash_token(refresh1)
        thash2 = hash_token(refresh2)
        tok1 = (await test_session.execute(select(RefreshToken).where(RefreshToken.token_hash == thash1))).scalar_one()
        tok2 = (await test_session.execute(select(RefreshToken).where(RefreshToken.token_hash == thash2))).scalar_one()
        assert tok1.revoked_at is not None
        assert tok2.revoked_at is not None

    @pytest.mark.asyncio
    async def test_rbac_manager_vs_admin_permissions(
        self, client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Test RBAC: Manager can create and edit products, but only Admin can delete."""
        # Create Manager
        manager = await _create_user_with_role(test_session, "manager_user@example.com", Role.manager)
        # Create Admin
        admin = await _create_user_with_role(test_session, "admin_user@example.com", Role.admin)

        # Login Manager
        m_login = await client.post("/auth/login", data={"username": manager.email, "password": "Secret123!"})
        m_token = m_login.json()["access_token"]

        # Manager creates a product -> SUCCESS 201
        prod_payload: dict[str, Any] = {
            "title": "Manager Tablet",
            "description": "Powerful tablet",
            "price": 499.99,
            "category": "Electronics",
            "stock_quantity": 25,
        }
        create_res = await client.post(
            "/products",
            headers={"Authorization": f"Bearer {m_token}"},
            json=prod_payload,
        )
        assert create_res.status_code == 201
        product_id: int = create_res.json()["id"]

        # Manager edits the product -> SUCCESS 200
        update_payload: dict[str, Any] = {
            "title": "Manager Tablet Pro",
            "description": "Powerful tablet upgraded",
            "price": 449.99,
            "category": "Electronics",
            "stock_quantity": 20,
            "is_active": True,
        }
        update_res = await client.put(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {m_token}"},
            json=update_payload,
        )
        assert update_res.status_code == 200
        assert float(update_res.json()["price"]) == 449.99

        # Manager tries to DELETE product -> FORBIDDEN 403 (Only admin may delete)
        m_delete_res = await client.delete(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {m_token}"},
        )
        assert m_delete_res.status_code == 403

        # Login Admin
        a_login = await client.post("/auth/login", data={"username": admin.email, "password": "Secret123!"})
        a_token = a_login.json()["access_token"]

        # Admin DELETES product -> SUCCESS 204
        a_delete_res = await client.delete(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {a_token}"},
        )
        assert a_delete_res.status_code == 204

    @pytest.mark.asyncio
    async def test_owner_and_self_protection(
        self, client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Test admin cannot deactivate/delete themselves, nor deactivate/delete the Main Owner."""
        # Find or create Main Owner (alosi4ek@gmail.com)
        owner_check = await test_session.execute(select(User).where(User.email == "alosi4ek@gmail.com"))
        owner = owner_check.scalar_one_or_none()
        if not owner:
            owner = await _create_user_with_role(test_session, "alosi4ek@gmail.com", Role.admin)

        # Create another secondary admin
        admin2 = await _create_user_with_role(test_session, "secondary_admin@example.com", Role.admin)

        # Login secondary admin
        login_res = await client.post("/auth/login", data={"username": admin2.email, "password": "Secret123!"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Admin tries to deactivate themselves -> 403 Forbidden
        self_deact = await client.patch(f"/admin/users/{admin2.id}", headers=headers, json={"is_active": False})
        assert self_deact.status_code == 403
        assert "deactivate yourself" in self_deact.json()["detail"].lower()

        # 2. Admin tries to delete themselves -> 403 Forbidden
        self_del = await client.delete(f"/admin/users/{admin2.id}", headers=headers)
        assert self_del.status_code == 403
        assert "cannot delete your own account" in self_del.json()["detail"].lower()

        # 3. Admin tries to deactivate Main Owner -> 403 Forbidden
        owner_deact = await client.patch(f"/admin/users/{owner.id}", headers=headers, json={"is_active": False})
        assert owner_deact.status_code == 403
        assert "owner" in owner_deact.json()["detail"].lower()

        # 4. Admin tries to delete Main Owner -> 403 Forbidden
        owner_del = await client.delete(f"/admin/users/{owner.id}", headers=headers)
        assert owner_del.status_code == 403
        assert "owner" in owner_del.json()["detail"].lower()

    def test_in_memory_rate_limiter_unit(self) -> None:
        """Test the sliding window RateLimiter raises TooManyRequestsError after limit is exceeded."""
        limiter = RateLimiter(limit=3, window_seconds=60)
        client_key = "192.168.1.100"

        # 3 requests allowed
        limiter.check(client_key)
        limiter.check(client_key)
        limiter.check(client_key)

        # 4th request must be rejected with 429
        with pytest.raises(TooManyRequestsError) as exc_info:
            limiter.check(client_key)

        assert exc_info.value.retry_after > 0
        assert exc_info.value.retry_after <= 60

        # Another client IP should still be allowed
        limiter.check("192.168.1.101")

    @pytest.mark.asyncio
    async def test_security_headers_present(self, client: AsyncClient) -> None:
        """Test that every HTTP response contains industrial security headers."""
        res = await client.get("/products")
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
