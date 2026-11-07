from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)
from app.services.cart import CartService

router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)


DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


@router.get(
    "",
    response_model=CartResponse,
)
async def get_cart(
    current_user: CurrentUser,
    session: DbSession,
):
    service = CartService(session)

    return await service.get_cart(current_user.id)


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_cart_item(
    data: CartItemCreate,
    current_user: CurrentUser,
    session: DbSession,
):
    service = CartService(session)

    return await service.add_item(
        current_user.id,
        data,
    )


@router.patch(
    "/items/{product_id}",
    response_model=CartItemResponse,
)
async def update_cart_item(
    product_id: str,
    data: CartItemUpdate,
    current_user: CurrentUser,
    session: DbSession,
):
    service = CartService(session)

    return await service.update_item(
        current_user.id,
        product_id,
        data,
    )


@router.delete(
    "/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_cart_item(
    product_id: str,
    current_user: CurrentUser,
    session: DbSession,
):
    service = CartService(session)

    await service.remove_item(
        current_user.id,
        product_id,
    )