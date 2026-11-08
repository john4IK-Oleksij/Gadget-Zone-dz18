from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    return password_hasher.verify(
        password,
        password_hash,
    )


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)

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
    now = datetime.now(UTC)

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