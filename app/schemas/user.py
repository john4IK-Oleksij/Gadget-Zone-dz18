from pydantic import BaseModel, ConfigDict

from app.enums import Role


class UserCreate(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role = Role.customer
    is_active: bool = True
    is_admin: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role = Role.customer
    is_active: bool = True
    is_admin: bool = False


class UserAdminUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None
