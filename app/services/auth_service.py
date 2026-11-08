import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    generate_refresh_token,
    hash_token,
    utcnow,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _ensure_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=utcnow().tzinfo)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def authenticate(self, email: str, password: str) -> User | None:
        stmt = select(User).where(User.email == email.strip().lower())
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            # Timing attack protection: perform constant-time dummy verification
            await verify_password(password, DUMMY_HASH)
            return None

        if not await verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        return user

    async def login(self, user: User) -> TokenPair:
        """Створює нову сесію входу з унікальним family_id."""
        return await self._issue_pair(user.id, family_id=uuid.uuid4().hex)

    async def refresh(self, raw_token: str | None) -> TokenPair | None:
        """
        Ротація токена з песимістичним блокуванням та виявленням крадіжки (Reuse Detection).
        """
        if not raw_token:
            return None

        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(raw_token))
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            return None

        # TOKEN REUSE DETECTION:
        # Якщо цим токеном уже скористалися або його відкликали — це компрометація сесії!
        # Негайно анулюємо всю родину (всі токени цього ланцюжка на пристрої).
        if record.used_at is not None or record.revoked_at is not None:
            await self._revoke_family(record.family_id)
            return None

        user = await self.session.get(User, record.user_id)
        if _ensure_utc(record.expires_at) <= utcnow() or user is None or not user.is_active:
            record.revoked_at = utcnow()
            await self.session.commit()
            return None

        # Позначаємо поточний токен як використаний
        record.used_at = utcnow()

        # Випускаємо новий токен у тій самій родині (family_id)
        return await self._issue_pair(user.id, family_id=record.family_id)

    async def logout(self, raw_token: str | None) -> None:
        """Відкликає сесію конкретного пристрою."""
        if not raw_token:
            return

        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(raw_token)
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is not None:
            await self._revoke_family(record.family_id)

    async def logout_all(self, user_id: int) -> None:
        """Відкликає всі активні сесії користувача з усіх пристроїв."""
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def _issue_pair(self, user_id: int, family_id: str) -> TokenPair:
        raw_refresh = generate_refresh_token()
        now = utcnow()
        new_token = RefreshToken(
            token_hash=hash_token(raw_refresh),
            family_id=family_id,
            user_id=user_id,
            expires_at=now + timedelta(days=settings.refresh_token_ttl_days),
        )
        self.session.add(new_token)
        await self.session.commit()

        access_token = create_access_token(user_id)
        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
        )

    async def _revoke_family(self, family_id: str) -> None:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
        await self.session.execute(stmt)
        await self.session.commit()
