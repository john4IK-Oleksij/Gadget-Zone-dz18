from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        category: str | None = None,
        skip: int = 0,
        limit: int = 8,
    ) -> list[Product]:
        query = select(Product)

        if category is not None:
            query = query.where(Product.category == category)

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_by_id(self, product_id: str) -> Product:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )

        product = result.scalar_one_or_none()

        if product is None:
            raise NotFoundError("Product not found")

        return product

    async def create(self, data: ProductCreate) -> Product:
        existing_product = await self.session.get(Product, data.id)

        if existing_product is not None:
            raise ConflictError(
                "Product with this id already exists"
            )

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
        await self.session.delete(product)
        await self.session.commit()