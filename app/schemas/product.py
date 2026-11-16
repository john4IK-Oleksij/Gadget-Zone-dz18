from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    title: str
    description: str
    image: str | None = None
    price: Decimal
    old_price: Decimal | None = None
    category: str
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductUpdate(BaseModel):
    title: str
    description: str
    image: str | None = None
    price: Decimal
    old_price: Decimal | None = None
    category: str
    stock_quantity: int = Field(ge=0)
    is_active: bool = True

class ProductPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    image: str | None = None
    price: Decimal | None = None
    old_price: Decimal | None = None
    category: str | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    image: str | None = None
    price: Decimal
    old_price: Decimal | None
    category: str
    stock_quantity: int
    is_active: bool = True
