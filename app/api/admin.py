from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import AdminUser
from app.schemas.admin import AdminStatsResponse
from app.schemas.product import ProductResponse
from app.schemas.user import AdminUserResponse, UserAdminUpdate
from app.services.admin import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


@router.get(
    "/users",
    response_model=list[AdminUserResponse],
)
async def get_users(
    admin: AdminUser,
    session: DbSession,
) -> list[AdminUserResponse]:
    service = AdminService(session)

    return await service.get_users()


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserResponse,
)
async def update_user(
    user_id: int,
    data: UserAdminUpdate,
    admin: AdminUser,
    session: DbSession,
) -> AdminUserResponse:
    service = AdminService(session)
    return await service.update_user(user_id, admin, data)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    admin: AdminUser,
    session: DbSession,
) -> None:
    service = AdminService(session)
    await service.delete_user(user_id, admin)


@router.get(
    "/products",
    response_model=list[ProductResponse],
)
async def get_products(
    admin: AdminUser,
    session: DbSession,
) -> list[ProductResponse]:
    service = AdminService(session)

    return await service.get_products()


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
)
async def get_stats(
    admin: AdminUser,
    session: DbSession,
) -> AdminStatsResponse:
    service = AdminService(session)

    return await service.get_stats()
