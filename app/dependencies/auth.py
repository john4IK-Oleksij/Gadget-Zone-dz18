from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.enums import Role
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

    if user is None or not user.is_active:
        raise credentials_exception

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


def require_roles(*roles: Role) -> Callable[[User], User]:
    """
    Фабрика залежностей FastAPI для перевірки ролей користувача (RBAC).
    Підтримує зворотну сумісність: якщо is_admin == True, надається роль admin.
    """
    def role_checker(current_user: CurrentUser) -> User:
        user_role = Role.admin if current_user.is_admin else current_user.role
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


async def require_admin(
    current_user: CurrentUser,
) -> User:
    """Сумісність: перевіряє права адміністратора."""
    if not (current_user.is_admin or current_user.role == Role.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


AdminUser = Annotated[
    User,
    Depends(require_admin),
]

ManagerUser = Annotated[
    User,
    Depends(require_roles(Role.admin, Role.manager)),
]

CustomerUser = Annotated[
    User,
    Depends(require_roles(Role.customer)),
]


async def require_non_admin(
    current_user: CurrentUser,
) -> User:
    if current_user.is_admin or current_user.role == Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot use cart",
        )
    return current_user


NonAdminUser = Annotated[
    User,
    Depends(require_non_admin),
]
