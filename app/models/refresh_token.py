from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, TypeDecorator

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


def utcnow() -> datetime:
    return datetime.now(UTC)


class UtcDateTime(TypeDecorator[datetime]):
    """MySQL/MariaDB не зберігає часовий пояс: записуємо в UTC, читаємо як UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            return value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is not None:
            return value.replace(tzinfo=UTC)
        return value


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    family_id: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        default=utcnow,
    )
    expires_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        default=None,
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        default=None,
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", backref="refresh_tokens")
