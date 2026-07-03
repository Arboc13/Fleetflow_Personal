import datetime as dt
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class ServiceRecord(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "service_records"
    __table_args__ = (
        CheckConstraint("cost >= 0", name="ck_service_cost_nonneg"),
        CheckConstraint("km_at_service >= 0", name="ck_service_km_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), index=True, nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    km_at_service: Mapped[int] = mapped_column(Integer, nullable=False)
    work_description: Mapped[str] = mapped_column(Text, nullable=False)
    parts_replaced: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
