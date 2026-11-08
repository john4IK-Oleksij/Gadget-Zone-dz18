from typing import Annotated

import os
import shutil
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import AdminUser
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import ProductService

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


@router.get("", response_model=list[ProductResponse])
async def get_products(
    session: DbSession,
    category: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(8, ge=1, le=100),
):
    service = ProductService(session)

    return await service.get_all(
        category=category,
        skip=skip,
        limit=limit,
    )


@router.get("/count")
async def get_products_count(
    session: DbSession,
    category: str | None = None,
):
    service = ProductService(session)
    count = await service.get_count(category=category)
    return {"count": count}


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: int,
    session: DbSession,
):
    service = ProductService(session)

    return await service.get_by_id(product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreate,
    session: DbSession,
    admin: AdminUser,
):
    service = ProductService(session)

    return await service.create(data)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: DbSession,
    admin: AdminUser,
):
    service = ProductService(session)

    product = await service.get_by_id(product_id, include_inactive=True)

    return await service.update(product, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    product_id: int,
    session: DbSession,
    admin: AdminUser,
):
    service = ProductService(session)

    product = await service.get_by_id(product_id, include_inactive=True)

    await service.delete(product)

@router.post(
    "/upload-image",
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    admin: AdminUser,
    file: UploadFile = File(...),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed",
        )

    ext = os.path.splitext(file.filename or "")[1].lower()
    if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]:
        ext = ".jpg"

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join("uploads", unique_filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"image_url": f"/uploads/{unique_filename}"}
