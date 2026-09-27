import datetime as dt

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.user import User


class Driver(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 1:1 link to a users row so the driver can log in.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # CNP is encrypted at rest (NFR-1) and only ever returned masked.
    cnp_encrypted: Mapped[str] = mapped_column(String(255), nullable=False)
    # HMAC of the CNP (crypto.cnp_fingerprint) — enforces one driver per CNP.
    cnp_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    license_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    license_series: Mapped[str | None] = mapped_column(String(10), nullable=True)
    license_category: Mapped[str] = mapped_column(String(20), nullable=False)
    license_expiry: Mapped[dt.date] = mapped_column(Date, nullable=False)

    user: Mapped[User] = relationship(lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Driver {self.id} user={self.user_id}>"
