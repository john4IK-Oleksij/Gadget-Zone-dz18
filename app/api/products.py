from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import AdminUser
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import ProductService

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


@router.get("", response_model=list[ProductResponse])
async def get_products(
    session: DbSession,
    category: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(8, ge=1, le=100),
):
    service = ProductService(session)

    return await service.get_all(
        category=category,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: str,
    session: DbSession,
):
    service = ProductService(session)

    return await service.get_by_id(product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreate,
    session: DbSession,
    admin: AdminUser,
):
    service = ProductService(session)

    return await service.create(data)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    session: DbSession,
    admin: AdminUser,
):
    service = ProductService(session)

    product = await service.get_by_id(product_id)

    return await service.update(product, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    product_id: str,
    session: DbSession,
    admin: AdminUser,
):
    service = ProductService(session)

    product = await service.get_by_id(product_id)

    await service.delete(product)