from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_count(
        self,
        category: str | None = None,
        include_inactive: bool = False,
    ) -> int:
        query = select(func.count(Product.id))

        if not include_inactive:
            query = query.where(Product.is_active.is_(True))

        if category is not None:
            query = query.where(Product.category == category)

        result = await self.session.execute(query)

        return result.scalar() or 0

    async def get_all(
        self,
        category: str | None = None,
        skip: int = 0,
        limit: int = 8,
        include_inactive: bool = False,
    ) -> list[Product]:
        query = select(Product)

        if not include_inactive:
            query = query.where(Product.is_active.is_(True))

        if category is not None:
            query = query.where(Product.category == category)

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_by_id(
        self,
        product_id: int,
        include_inactive: bool = False,
    ) -> Product:
        query = select(Product).where(Product.id == product_id)

        if not include_inactive:
            query = query.where(Product.is_active.is_(True))

        result = await self.session.execute(query)

        product = result.scalar_one_or_none()

        if product is None:
            raise NotFoundError("Product not found")

        return product

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())

        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)

        return product

    async def update(
        self,
        product: Product,
        data: ProductUpdate,
    ) -> Product:
        for field, value in data.model_dump().items():
            setattr(product, field, value)

        await self.session.commit()
        await self.session.refresh(product)

        return product

    async def delete(self, product: Product) -> None:
        # Soft delete: marks product as inactive so it disappears from catalog,
        # but preserves cart items with "Знято з продажу" and historical integrity.
        product.is_active = False
        await self.session.commit()
        await self.session.refresh(product)
