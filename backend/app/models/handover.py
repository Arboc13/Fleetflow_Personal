import enum

from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class HandoverDirection(str, enum.Enum):
    handover = "handover"  # vehicle given to the driver
    return_ = "return"  # vehicle returned by the driver


class HandoverStatus(str, enum.Enum):
    draft = "draft"
    closed = "closed"


class HandoverReport(Base, TimestampMixin, SoftDeleteMixin):
    """Proces-verbal de predare/primire. Immutable once closed (rule 2.3)."""

    __tablename__ = "handover_reports"
    __table_args__ = (
        CheckConstraint("km >= 0", name="ck_handover_km_nonneg"),
        CheckConstraint(
            "fuel_level_pct >= 0 AND fuel_level_pct <= 100", name="ck_handover_fuel_pct"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    allocation_id: Mapped[int] = mapped_column(
        ForeignKey("allocations.id"), index=True, nullable=False
    )
    direction: Mapped[HandoverDirection] = mapped_column(
        SAEnum(
            HandoverDirection,
            name="handover_direction",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    km: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_level_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    visual_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleanliness: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[HandoverStatus] = mapped_column(
        SAEnum(HandoverStatus, name="handover_status"),
        nullable=False,
        default=HandoverStatus.draft,
    )
