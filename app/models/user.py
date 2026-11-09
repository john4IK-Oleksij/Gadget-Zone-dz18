from typing import Any

from sqlalchemy import Boolean, Enum, String, false, true
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base
from app.enums import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, length=20),
        default=Role.customer,
        server_default=Role.customer.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
    )

    def __init__(self, **kwargs: Any) -> None:
        if "role" in kwargs and "is_admin" not in kwargs:
            kwargs["is_admin"] = (kwargs["role"] == Role.admin)
        elif "is_admin" in kwargs and "role" not in kwargs:
            kwargs["role"] = Role.admin if kwargs["is_admin"] else Role.customer
        super().__init__(**kwargs)

    @validates("role")
    def sync_role_to_is_admin(self, key: str, value: Role | str) -> Role:
        parsed_role = Role(value)
        expected_admin = (parsed_role == Role.admin)
        if self.__dict__.get("is_admin") != expected_admin:
            self.__dict__["is_admin"] = expected_admin
        return parsed_role

    @validates("is_admin")
    def sync_is_admin_to_role(self, key: str, value: bool) -> bool:
        expected_role = Role.admin if value else Role.customer
        if self.__dict__.get("role") != expected_role:
            self.__dict__["role"] = expected_role
        return bool(value)
