import datetime as dt
import enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class TripStatus(str, enum.Enum):
    draft = "draft"
    closed = "closed"


class TripSheet(Base, TimestampMixin, SoftDeleteMixin):
    """Foaie de parcurs. Immutable once closed (rule 2.3)."""

    __tablename__ = "trip_sheets"
    __table_args__ = (
        CheckConstraint("end_km IS NULL OR end_km > start_km", name="ck_trip_km"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), index=True, nullable=False
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id"), index=True, nullable=False
    )
    departure_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    arrival_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    start_km: Mapped[int] = mapped_column(Integer, nullable=False)
    end_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[TripStatus] = mapped_column(
        SAEnum(TripStatus, name="trip_status"),
        nullable=False,
        default=TripStatus.draft,
    )
