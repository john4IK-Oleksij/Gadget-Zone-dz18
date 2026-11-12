from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.user import UserChangePassword, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/me/change-password")
async def change_password(
    data: UserChangePassword,
    current_user: CurrentUser,
    session: DbSession,
) -> dict[str, str]:
    """Зміна пароля поточного користувача (з перевіркою старого пароля)."""
    if not await verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long",
        )

    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be identical to the current password",
        )

    current_user.password_hash = await hash_password(data.new_password)
    await session.commit()

    return {"detail": "Password successfully updated"}
