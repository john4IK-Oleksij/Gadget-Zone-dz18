from fastapi import APIRouter

from app.schemas.product import ProductResponse

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductResponse])
async def get_products():
    return [
        {"id": 1, "name": "iPhone"},
        {"id": 2, "name": "MacBook"},
    ]