from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.product import Product
from app.models.user import User
from app.schemas.admin import AdminStatsResponse
from app.schemas.product import ProductResponse
from app.schemas.user import AdminUserResponse, UserAdminUpdate
from app.services.auth_service import revoke_user_tokens


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

    async def update_user(
        self,
        user_id: int,
        actor: User,
        data: UserAdminUpdate,
    ) -> AdminUserResponse:
        user = await self.session.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found")

        changes = data.model_dump(exclude_unset=True)
        if user.id == actor.id and any(k in changes for k in ("role", "is_active")):
            raise ForbiddenError("Cannot change your own role or deactivate yourself")

        # Захист Головного Власника (Owner): ніхто не може понизити чи заблокувати обліковий запис власника
        is_owner = (user.id == 2 or user.email == "alosi4ek@gmail.com")
        if is_owner and actor.id != user.id and any(k in changes for k in ("role", "is_active")):
            raise ForbiddenError("Cannot modify the role or status of the system owner")

        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
            if not data.is_active:
                await revoke_user_tokens(self.session, user.id)

        await self.session.commit()
        await self.session.refresh(user)
        return AdminUserResponse.model_validate(user)

    async def delete_user(
        self,
        user_id: int,
        actor: User,
    ) -> None:
        user = await self.session.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found")

        if user.id == actor.id:
            raise ForbiddenError("Cannot delete your own account")

        # Захист Головного Власника (Owner): ніхто не може видалити акаунт власника
        if user.id == 2 or user.email == "alosi4ek@gmail.com":
            raise ForbiddenError("Cannot delete the system owner account")

        await self.session.delete(user)
        await self.session.commit()

    async def get_products(self) -> list[ProductResponse]:
        result = await self.session.execute(
            select(Product).order_by(Product.id)
        )

        products = result.scalars().all()

        return [
            ProductResponse.model_validate(product)
            for product in products
        ]

    async def get_stats(self) -> AdminStatsResponse:
        users_count = await self.session.scalar(
            select(func.count(User.id))
        )

        products_count = await self.session.scalar(
            select(func.count(Product.id))
        )

        return AdminStatsResponse(
            users_count=users_count or 0,
            products_count=products_count or 0,
        )
