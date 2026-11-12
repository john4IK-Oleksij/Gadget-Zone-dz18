import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()
# Захист від атак за часом (Timing Attack): згенерований еталонний хеш для неіснуючих користувачів
DUMMY_HASH: str = password_hasher.hash("timing-attack-protection-dummy-password")


def utcnow() -> datetime:
    return datetime.now(UTC)


async def hash_password(password: str) -> str:
    """Хешує пароль у фоновому потоці (не блокуючи asyncio event loop)."""
    return await asyncio.to_thread(password_hasher.hash, password)


async def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Перевіряє пароль у фоновому потоці (не блокуючи asyncio event loop)."""
    return await asyncio.to_thread(
        password_hasher.verify,
        password,
        password_hash,
    )


def generate_refresh_token() -> str:
    """Генерує криптографічно стійкий випадковий рядок для Refresh Token (64 символи)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Обчислює SHA-256 хеш токена для безпечного збереження в базі даних."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: int) -> str:
    now = utcnow()

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_ttl_minutes,
        ),
    }

    return jwt.encode(  # type: ignore[reportUnknownMemberType]
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: int) -> str:
    """Сумісність: створює JWT рефреш-токен, якщо потрібен у старому форматі."""
    now = utcnow()

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(
            days=settings.refresh_token_ttl_days,
        ),
        "type": "refresh",
    }

    return jwt.encode(  # type: ignore[reportUnknownMemberType]
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(  # type: ignore[reportUnknownMemberType]
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={
            "require": ["exp", "sub"],
        },
    )

    return payload
