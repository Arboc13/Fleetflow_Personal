import datetime as dt
import enum
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class DocumentType(str, enum.Enum):
    RCA = "RCA"
    CASCO = "CASCO"
    ITP = "ITP"
    ROVINIETA = "Rovinieta"


class VehicleDocument(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "vehicle_documents"
    __table_args__ = (
        CheckConstraint("cost >= 0", name="ck_document_cost_nonneg"),
        CheckConstraint("expiry_date > issue_date", name="ck_document_dates"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), index=True, nullable=False
    )
    type: Mapped[DocumentType] = mapped_column(
        SAEnum(
            DocumentType,
            name="document_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    series_number: Mapped[str] = mapped_column(String(50), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    issue_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
