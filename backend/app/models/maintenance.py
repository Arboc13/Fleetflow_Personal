import datetime as dt

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class MaintenanceRule(Base, TimestampMixin, SoftDeleteMixin):
    """Dual km/time service interval (rule 2.2). Feeds the alert engine."""

    __tablename__ = "maintenance_rules"
    __table_args__ = (
        CheckConstraint("interval_km > 0", name="ck_rule_interval_km_positive"),
        CheckConstraint("interval_months > 0", name="ck_rule_interval_months_positive"),
        CheckConstraint("last_service_km >= 0", name="ck_rule_last_km_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Service")
    interval_km: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_months: Mapped[int] = mapped_column(Integer, nullable=False)
    last_service_km: Mapped[int] = mapped_column(Integer, nullable=False)
    last_service_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
