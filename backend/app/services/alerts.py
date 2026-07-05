"""Predictive alert engine (rule 2.2, F-502).

Scans document/license expiries (30/15/5-day thresholds) and the maintenance
dual km+time rule, emitting deduplicated notifications. Pure function
`run_alert_scan(db)` is called by the daily APScheduler job, the on-demand
endpoint, and after a fuel import.
"""
from __future__ import annotations

import calendar
import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.document import VehicleDocument
from app.models.driver import Driver
from app.models.maintenance import MaintenanceRule
from app.models.notification import Notification, Severity
from app.models.trip_sheet import TripSheet, TripStatus
from app.models.user import Role, User
from app.models.vehicle import Vehicle

MAINT_KM_THRESHOLD = 1000
MAINT_DAYS_THRESHOLD = 30


def add_months(d: dt.date, months: int) -> dt.date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)


def _managers_and_admins(db: Session) -> list[int]:
    rows = db.scalars(
        select(User.id).where(
            User.is_active.is_(True),
            User.role.in_([Role.admin, Role.fleet_manager]),
        )
    ).all()
    return list(rows)


def _expiry_stage(days_left: int) -> tuple[str, Severity] | None:
    """Map days-until-expiry to an alert stage (30/15/5). None = no alert yet."""
    if days_left <= 5:
        return "5", Severity.critical
    if days_left <= 15:
        return "15", Severity.warning
    if days_left <= 30:
        return "30", Severity.warning
    return None


def _expiry_phrase(days_left: int, expiry: dt.date) -> str:
    if days_left < 0:
        return f"expired {-days_left} day(s) ago ({expiry})"
    return f"expires in {days_left} day(s) ({expiry})"


def compute_avg_daily_km(db: Session, vehicle_id: int) -> float:
    """Average km/day over the last 30 days of closed trip sheets (0 = cold start)."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    sheets = db.scalars(
        select(TripSheet).where(
            TripSheet.vehicle_id == vehicle_id,
            TripSheet.status == TripStatus.closed,
            TripSheet.deleted_at.is_(None),
            TripSheet.departure_at >= cutoff,
        )
    ).all()
    total = sum(
        (s.end_km - s.start_km)
        for s in sheets
        if s.end_km is not None and s.start_km is not None
    )
    return total / 30 if total else 0.0


def _emit(
    db: Session,
    recipients: list[int],
    *,
    type_: str,
    severity: Severity,
    message: str,
    entity_type: str,
    entity_id: int,
    dedup_key: str,
) -> int:
    created = 0
    for uid in set(recipients):
        exists = db.scalar(
            select(Notification.id).where(
                Notification.user_id == uid, Notification.dedup_key == dedup_key
            )
        )
        if exists:
            continue
        db.add(
            Notification(
                user_id=uid,
                type=type_,
                severity=severity,
                message=message,
                entity_type=entity_type,
                entity_id=entity_id,
                dedup_key=dedup_key,
            )
        )
        created += 1
    return created


def _scan_documents(db: Session, today: dt.date, recipients: list[int]) -> int:
    created = 0
    docs = db.scalars(
        select(VehicleDocument).where(VehicleDocument.deleted_at.is_(None))
    ).all()
    for doc in docs:
        days_left = (doc.expiry_date - today).days
        stage = _expiry_stage(days_left)
        if stage is None:
            continue
        label, severity = stage
        vehicle = db.get(Vehicle, doc.vehicle_id)
        plate = vehicle.plate if vehicle else f"vehicle {doc.vehicle_id}"
        message = (
            f"{doc.type.value} ({doc.series_number}) for {plate} "
            f"{_expiry_phrase(days_left, doc.expiry_date)}"
        )
        created += _emit(
            db,
            recipients,
            type_="document_expiry",
            severity=severity,
            message=message,
            entity_type="vehicle_document",
            entity_id=doc.id,
            # Expiry date in the key lets alerts fire again after a renewal.
            dedup_key=f"document:{doc.id}:{doc.expiry_date}:{label}",
        )
    return created


def _scan_licenses(db: Session, today: dt.date, recipients: list[int]) -> int:
    created = 0
    drivers = db.scalars(select(Driver).where(Driver.deleted_at.is_(None))).all()
    for driver in drivers:
        days_left = (driver.license_expiry - today).days
        stage = _expiry_stage(days_left)
        if stage is None:
            continue
        label, severity = stage
        message = (
            f"Driving licence {driver.license_number} "
            f"{_expiry_phrase(days_left, driver.license_expiry)}"
        )
        # Managers/admins plus the driver themselves.
        targets = recipients + [driver.user_id]
        created += _emit(
            db,
            targets,
            type_="license_expiry",
            severity=severity,
            message=message,
            entity_type="driver",
            entity_id=driver.id,
            dedup_key=f"license:{driver.id}:{driver.license_expiry}:{label}",
        )
    return created


def _scan_maintenance(db: Session, today: dt.date, recipients: list[int]) -> int:
    created = 0
    rules = db.scalars(
        select(MaintenanceRule).where(MaintenanceRule.deleted_at.is_(None))
    ).all()
    for rule in rules:
        vehicle = db.get(Vehicle, rule.vehicle_id)
        if vehicle is None:
            continue
        km_to_due = (rule.last_service_km + rule.interval_km) - vehicle.current_km
        days_to_due = (add_months(rule.last_service_date, rule.interval_months) - today).days
        if not (km_to_due < MAINT_KM_THRESHOLD or days_to_due < MAINT_DAYS_THRESHOLD):
            continue

        overdue = km_to_due < 0 or days_to_due < 0
        severity = Severity.critical if overdue else Severity.warning
        # First condition wins: km takes priority over time.
        reason = (
            f"{km_to_due} km to service"
            if km_to_due < MAINT_KM_THRESHOLD
            else f"{days_to_due} day(s) to service"
        )

        # Cold-start guard: skip the estimate when avg daily km is unknown/zero.
        avg = compute_avg_daily_km(db, vehicle.id)
        estimate = ""
        if avg > 0 and km_to_due > 0:
            estimate = f" (~{round(km_to_due / avg)} day(s) at current usage)"

        label = "overdue" if overdue else "due"
        message = f"Service '{rule.name}' for {vehicle.plate}: {reason}{estimate}"
        created += _emit(
            db,
            recipients,
            type_="maintenance_due",
            severity=severity,
            message=message,
            entity_type="maintenance_rule",
            entity_id=rule.id,
            # Last-service data in the key lets alerts fire again next cycle.
            dedup_key=f"maintenance:{rule.id}:{rule.last_service_date}:{rule.last_service_km}:{label}",
        )
    return created


def run_alert_scan(db: Session) -> int:
    """Run all scans and persist new notifications. Returns the count created."""
    today = dt.date.today()
    recipients = _managers_and_admins(db)
    created = 0
    created += _scan_documents(db, today, recipients)
    created += _scan_licenses(db, today, recipients)
    created += _scan_maintenance(db, today, recipients)
    db.commit()
    return created


def run_alert_scan_in_background() -> None:
    """Entry point for APScheduler / BackgroundTasks — owns its own session.

    Best-effort: never raises, so it can never block or fail a request (F-501).
    """
    db = SessionLocal()
    try:
        run_alert_scan(db)
    except Exception:  # noqa: BLE001
        db.rollback()
    finally:
        db.close()
