import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.cart import router as cart_router
from app.api.products import router as products_router
from app.api.users import router as users_router
from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(
        f"Connecting to database: host={engine.url.host}, port={engine.url.port}, db={engine.url.database}"
    )
    await init_db(engine)
    print("Database tables initialized successfully!")
    yield


app = FastAPI(
    title="Gadget Zone API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(
    request: Request,
    exc: ForbiddenError,
):
    return JSONResponse(
        status_code=403,
        content={"detail": exc.message},
    )


app.include_router(auth_router)
app.include_router(products_router)
app.include_router(users_router)
app.include_router(cart_router)
app.include_router(admin_router)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if os.path.exists("front"):
    app.mount("/front", StaticFiles(directory="front", html=True), name="front")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/front/index.html")


@app.get("/db-test")
async def db_test():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        return {"database": result.scalar_one()}
