from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.cart_item import CartItem
from app.models.product import Product
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)


class CartService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cart(self, user_id: int) -> CartResponse:
        result = await self.session.execute(
            select(CartItem, Product)
            .join(
                Product,
                Product.id == CartItem.product_id,
            )
            .where(CartItem.user_id == user_id)
        )

        rows = result.all()

        return CartResponse(
            items=[
                CartItemResponse(
                    product_id=item.product_id,
                    title=product.title,
                    image=product.image,
                    price=product.price,
                    stock_quantity=product.stock_quantity,
                    quantity=item.quantity,
                )
                for item, product in rows
            ],
            total_items=sum(
                item.quantity
                for item, _ in rows
            ),
        )

    async def add_item(
        self,
        user_id: int,
        data: CartItemCreate,
    ) -> CartItemResponse:
        product = await self.session.get(
            Product,
            data.product_id,
        )

        if product is None:
            raise NotFoundError("Product not found")

        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == data.product_id,
            )
        )

        item = result.scalar_one_or_none()

        if item is not None:
            item.quantity += data.quantity
        else:
            item = CartItem(
                user_id=user_id,
                product_id=data.product_id,
                quantity=data.quantity,
            )
            self.session.add(item)

        await self.session.commit()
        await self.session.refresh(item)

        return CartItemResponse(
            product_id=item.product_id,
            title=product.title,
            image=product.image,
            price=product.price,
            stock_quantity=product.stock_quantity,
            quantity=item.quantity,
        )

    async def update_item(
        self,
        user_id: int,
        product_id: str,
        data: CartItemUpdate,
    ) -> CartItemResponse:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )

        item = result.scalar_one_or_none()

        if item is None:
            raise NotFoundError("Cart item not found")

        product = await self.session.get(Product, product_id)

        if product is None:
            raise NotFoundError("Product not found")

        item.quantity = data.quantity

        await self.session.commit()
        await self.session.refresh(item)

        return CartItemResponse(
            product_id=item.product_id,
            title=product.title,
            image=product.image,
            price=product.price,
            stock_quantity=product.stock_quantity,
            quantity=item.quantity,
        )

    async def remove_item(
        self,
        user_id: int,
        product_id: str,
    ) -> None:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )

        item = result.scalar_one_or_none()

        if item is None:
            raise NotFoundError("Cart item not found")

        await self.session.delete(item)
        await self.session.commit()