from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import clear_refresh_cookie, set_refresh_cookie
from app.core.security import hash_password
from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreate,
    session: DbSession,
) -> User:
    result = await session.execute(
        select(User).where(User.email == data.email)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        email=data.email,
        password_hash=await hash_password(data.password),
        is_admin=False,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    response: Response,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    session: DbSession,
) -> dict[str, str]:
    service = AuthService(session)
    user = await service.authenticate(form_data.username, form_data.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    pair = await service.login(user)
    set_refresh_cookie(response, pair.refresh_token)

    return {
        "access_token": pair.access_token,
        "refresh_token": pair.refresh_token,
        "token_type": pair.token_type,
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_tokens(
    request: Request,
    response: Response,
    session: DbSession,
    body: RefreshTokenRequest | None = None,
) -> dict[str, str]:
    raw_token = (body and body.refresh_token) or request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    service = AuthService(session)
    pair = await service.refresh(raw_token)
    if pair is None:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    set_refresh_cookie(response, pair.refresh_token)

    return {
        "access_token": pair.access_token,
        "refresh_token": pair.refresh_token,
        "token_type": pair.token_type,
    }


@router.post(
    "/logout",
)
async def logout(
    request: Request,
    response: Response,
    session: DbSession,
    body: RefreshTokenRequest | None = None,
) -> dict[str, str]:
    """Вихід з поточного пристрою (відкликає конкретну сесію refresh token)."""
    raw_token = (body and body.refresh_token) or request.cookies.get("refresh_token")
    service = AuthService(session)
    await service.logout(raw_token)
    clear_refresh_cookie(response)
    return {"detail": "Successfully logged out"}


@router.post(
    "/logout-all",
)
async def logout_all(
    response: Response,
    current_user: CurrentUser,
    session: DbSession,
) -> dict[str, str]:
    """Вихід з усіх пристроїв (відкликає всі активні сесії користувача)."""
    service = AuthService(session)
    await service.logout_all(current_user.id)
    clear_refresh_cookie(response)
    return {"detail": "All sessions have been revoked"}
