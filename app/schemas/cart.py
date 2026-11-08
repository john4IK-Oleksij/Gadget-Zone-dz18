from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    product_id: int
    title: str
    image: str | None
    price: Decimal
    stock_quantity: int
    quantity: int
    is_active: bool = True


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[CartItemResponse]
    total_items: int
