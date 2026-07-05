import datetime as dt
import enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class AllocationType(str, enum.Enum):
    permanent = "permanent"
    trip = "trip"


class AllocationStatus(str, enum.Enum):
    active = "active"
    ended = "ended"  # set when the return handover report is closed


class Allocation(Base, TimestampMixin, SoftDeleteMixin):
    """Vehicle↔driver assignment over a period (rule 2.1: no overlaps).

    The period is start_at..end_at (NULL end = open-ended). Overlap is
    rejected in the service layer (friendly 409) AND by Postgres EXCLUDE
    constraints in migration 0006, which make rule 2.1 concurrency-safe.
    """

    __tablename__ = "allocations"
    __table_args__ = (
        CheckConstraint("end_at IS NULL OR end_at > start_at", name="ck_allocation_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), index=True, nullable=False
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id"), index=True, nullable=False
    )
    start_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    type: Mapped[AllocationType] = mapped_column(
        SAEnum(AllocationType, name="allocation_type"), nullable=False
    )
    status: Mapped[AllocationStatus] = mapped_column(
        SAEnum(AllocationStatus, name="allocation_status"),
        nullable=False,
        default=AllocationStatus.active,
    )
