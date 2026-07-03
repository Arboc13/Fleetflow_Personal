import enum

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Role(str, enum.Enum):
    admin = "admin"
    fleet_manager = "fleet_manager"
    driver = "driver"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="user_role"), nullable=False, default=Role.driver
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.id} {self.email} ({self.role.value})>"
