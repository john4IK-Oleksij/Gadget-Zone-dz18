from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.products import router as products_router
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(engine)
    yield


app = FastAPI(
    title="Gadget Zone API",
    lifespan=lifespan,
)

app.include_router(products_router)


@app.get("/db-test")
async def db_test():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        return {"database": result.scalar_one()}