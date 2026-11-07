from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductResponse
from app.schemas.user import AdminUserResponse


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_users(self) -> list[AdminUserResponse]:
        result = await self.session.execute(
            select(User).order_by(User.id)
        )

        users = result.scalars().all()

        return [
            AdminUserResponse.model_validate(user)
            for user in users
        ]

    async def get_products(self) -> list[ProductResponse]:
        result = await self.session.execute(
            select(Product).order_by(Product.id)
        )

        products = result.scalars().all()

        return [
            ProductResponse.model_validate(product)
            for product in products
        ]

    async def get_stats(self) -> dict[str, int]:
        users_count = await self.session.scalar(
            select(func.count(User.id))
        )

        products_count = await self.session.scalar(
            select(func.count(Product.id))
        )

        return {
            "users_count": users_count or 0,
            "products_count": products_count or 0,
        }