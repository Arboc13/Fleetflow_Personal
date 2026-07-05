import datetime as dt
import enum

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Severity(str, enum.Enum):
    warning = "warning"  # yellow dashboard indicator
    critical = "critical"  # red dashboard indicator


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    # dedup_key makes each alert stage fire once per recipient (rule 2.2).
    __table_args__ = (
        UniqueConstraint("user_id", "dedup_key", name="uq_notification_user_dedup"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[Severity] = mapped_column(
        SAEnum(Severity, name="notification_severity"), nullable=False
    )
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dedup_key: Mapped[str] = mapped_column(String(150), nullable=False)
    read_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
