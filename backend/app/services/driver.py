import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.crypto import cnp_fingerprint, decrypt, encrypt, mask_cnp
from app.core.security import hash_password
from app.models.driver import Driver
from app.models.user import Role, User
from app.schemas.driver import DriverCreate, DriverRead, DriverUpdate


def build_driver_read(driver: Driver) -> DriverRead:
    """Serialize a driver, decrypting the CNP only to mask it (NFR-1)."""
    return DriverRead(
        id=driver.id,
        user_id=driver.user_id,
        email=driver.user.email,
        full_name=driver.user.full_name,
        phone=driver.phone,
        cnp_masked=mask_cnp(decrypt(driver.cnp_encrypted)),
        license_number=driver.license_number,
        license_series=driver.license_series,
        license_category=driver.license_category,
        license_expiry=driver.license_expiry,
        is_active=driver.user.is_active,
    )


def list_drivers(db: Session, *, include_deleted: bool = False) -> list[Driver]:
    stmt = select(Driver)
    if not include_deleted:
        stmt = stmt.where(Driver.deleted_at.is_(None))
    return list(db.scalars(stmt.order_by(Driver.id)))


def get_driver(db: Session, driver_id: int, *, include_deleted: bool = False) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None or (driver.deleted_at is not None and not include_deleted):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


def _ensure_unique(
    db: Session,
    *,
    cnp_hash: str | None = None,
    license_number: str | None = None,
    exclude_id: int | None = None,
) -> None:
    """409 on a duplicate CNP / license number (DB unique constraints back this up)."""
    checks = [
        (Driver.cnp_hash, cnp_hash, "A driver with this CNP already exists."),
        (Driver.license_number, license_number, "A driver with this license number already exists."),
    ]
    for column, value, message in checks:
        if value is None:
            continue
        stmt = select(Driver.id).where(column == value)
        if exclude_id is not None:
            stmt = stmt.where(Driver.id != exclude_id)
        if db.scalar(stmt) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def create_driver(db: Session, data: DriverCreate) -> Driver:
    cnp_hash = cnp_fingerprint(data.cnp)
    _ensure_unique(db, cnp_hash=cnp_hash, license_number=data.license_number)

    # Create the login account and the driver profile in one transaction.
    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=Role.driver,
    )
    db.add(user)
    try:
        db.flush()  # assign user.id without committing
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc

    driver = Driver(
        user_id=user.id,
        phone=data.phone,
        cnp_encrypted=encrypt(data.cnp),
        cnp_hash=cnp_hash,
        license_number=data.license_number,
        license_series=data.license_series,
        license_category=data.license_category,
        license_expiry=data.license_expiry,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


def update_driver(db: Session, driver_id: int, data: DriverUpdate) -> Driver:
    driver = get_driver(db, driver_id)
    changes = data.model_dump(exclude_unset=True)
    cnp = changes.pop("cnp", None)
    cnp_hash = cnp_fingerprint(cnp) if cnp is not None else None
    _ensure_unique(
        db,
        cnp_hash=cnp_hash,
        license_number=changes.get("license_number"),
        exclude_id=driver.id,
    )

    if cnp is not None:
        driver.cnp_encrypted = encrypt(cnp)
        driver.cnp_hash = cnp_hash
    for field, value in changes.items():
        setattr(driver, field, value)

    db.commit()
    db.refresh(driver)
    return driver


def soft_delete_driver(db: Session, driver_id: int) -> None:
    """Hide a driver and disable their login (Fleet Manager + Admin)."""
    driver = get_driver(db, driver_id)
    driver.deleted_at = dt.datetime.now(dt.timezone.utc)
    driver.user.is_active = False
    db.commit()


def hard_delete_driver(db: Session, driver_id: int) -> None:
    """Permanently delete a driver and their login (Admin only)."""
    driver = get_driver(db, driver_id, include_deleted=True)
    user = driver.user
    db.delete(driver)
    db.delete(user)
    db.commit()
