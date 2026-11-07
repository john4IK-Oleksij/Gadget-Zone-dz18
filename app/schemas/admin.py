from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    users_count: int
    products_count: int