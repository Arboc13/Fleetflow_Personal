import datetime as dt
import enum
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ImportStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ImportBatch(Base, TimestampMixin):
    """One fuel-file upload. Tracks progress and per-row rejection report (F-402)."""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(
        SAEnum(ImportStatus, name="import_status"),
        nullable=False,
        default=ImportStatus.pending,
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # List of {"row": int, "error": str, "data": {...}} for rejected rows.
    error_report: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class FuelTransaction(Base, TimestampMixin):
    __tablename__ = "fuel_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), index=True, nullable=False
    )
    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    liters: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    odometer_reported: Mapped[int | None] = mapped_column(Integer, nullable=True)
    station: Mapped[str | None] = mapped_column(String(120), nullable=True)
    import_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_batches.id"), index=True, nullable=True
    )
    is_suspect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    suspect_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
