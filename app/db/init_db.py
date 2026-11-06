from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.models import Product


async def init_db(engine: AsyncEngine) -> None:
    _ = Product

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)