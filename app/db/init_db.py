import asyncio
import json
import os
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.db.base import Base
from app.models import CartItem, Product, RefreshToken, User

# Ensure all models are registered on Base metadata
_ALL_MODELS = (CartItem, Product, RefreshToken, User)


def _load_seed_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def init_db(engine: AsyncEngine) -> None:
    # 1. Create tables if they do not exist
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    seed_file_path = os.path.join(
        os.path.dirname(__file__), "seed_75_products.json"
    )
    if not os.path.exists(seed_file_path):
        return

    data = await asyncio.to_thread(_load_seed_json, seed_file_path)

    products_data: list[dict[str, Any]] = data.get("products", [])
    users_data: list[dict[str, Any]] = data.get("users", [])

    async with session_maker() as session:
        # Check current products count
        count_res = await session.execute(select(func.count(Product.id)))
        current_count = count_res.scalar_one()

        # If empty or fewer than 75 products (e.g. only temporary 12 existed), sync all 75 products
        if current_count < len(products_data):
            # Clear any temporary products
            await session.execute(delete(Product))
            for p in products_data:
                product = Product(
                    id=p["id"],
                    title=p["title"],
                    description=p["description"],
                    image=p["image"],
                    price=Decimal(str(p["price"])),
                    old_price=Decimal(str(p["old_price"]))
                    if p.get("old_price") is not None
                    else None,
                    category=p["category"],
                    stock_quantity=p.get("stock_quantity", 0),
                    is_active=bool(p.get("is_active", True)),
                )
                session.add(product)
            await session.commit()

        # Sync user accounts (including admin with original password hash)
        for u in users_data:
            existing_user_res = await session.execute(
                select(User).where(User.email == u["email"])
            )
            existing_user = existing_user_res.scalar_one_or_none()
            if existing_user:
                # Update password hash and admin status to match local DB
                existing_user.password_hash = u["password_hash"]
                existing_user.is_admin = bool(u.get("is_admin", False))
            else:
                new_user = User(
                    id=u["id"],
                    email=u["email"],
                    password_hash=u["password_hash"],
                    is_admin=bool(u.get("is_admin", False)),
                )
                session.add(new_user)
        await session.commit()
