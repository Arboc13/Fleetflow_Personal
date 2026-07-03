import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.crypto import decrypt, encrypt, mask_cnp
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


def create_driver(db: Session, data: DriverCreate) -> Driver:
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

    if "cnp" in changes:
        driver.cnp_encrypted = encrypt(changes.pop("cnp"))
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
