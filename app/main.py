from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.core.exceptions import ConflictError, NotFoundError
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


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(
    request: Request,
    exc: NotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )


@app.exception_handler(ConflictError)
async def conflict_exception_handler(
    request: Request,
    exc: ConflictError,
):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )


app.include_router(auth_router)
app.include_router(products_router)


@app.get("/db-test")
async def db_test():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        return {"database": result.scalar_one()}