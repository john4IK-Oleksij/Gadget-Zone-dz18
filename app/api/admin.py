from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import AdminUser
from app.schemas.admin import AdminStatsResponse
from app.schemas.product import ProductResponse
from app.schemas.user import AdminUserResponse
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
):
    service = AdminService(session)

    return await service.get_users()


@router.get(
    "/products",
    response_model=list[ProductResponse],
)
async def get_products(
    admin: AdminUser,
    session: DbSession,
):
    service = AdminService(session)

    return await service.get_products()


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
)
async def get_stats(
    admin: AdminUser,
    session: DbSession,
):
    service = AdminService(session)

    return await service.get_stats()