from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


async def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise credentials_exception from None

    user = await session.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


async def require_admin(
    current_user: CurrentUser,
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


AdminUser = Annotated[
    User,
    Depends(require_admin),
]