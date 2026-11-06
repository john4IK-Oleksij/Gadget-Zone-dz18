from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    id: str
    title: str
    description: str
    image: str | None = None
    price: Decimal
    old_price: Decimal | None = None
    category: str
    stock_quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    title: str
    description: str
    image: str | None = None
    price: Decimal
    old_price: Decimal | None = None
    category: str
    stock_quantity: int = Field(ge=0)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    image: str | None = None
    price: Decimal
    old_price: Decimal | None
    category: str
    stock_quantity: int