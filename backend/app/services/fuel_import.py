"""Fuel-import parser (F-402, NFR-2).

Reads a CSV/XLSX with columns:
    date, plate, fuel_card, liters, price, odometer, station
Reconciles each row to a vehicle by plate OR fuel card. Rows that fail
validation are rejected into the batch error report; valid rows (including
flagged suspects) are committed in ONE transaction so a crash mid-import
rolls back cleanly with no partial data.
"""
from __future__ import annotations

import datetime as dt
import math
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.fuel import FuelTransaction, ImportBatch, ImportStatus
from app.models.vehicle import Vehicle

# Odometer more than this many km above the vehicle's current reading is suspect.
IMPLAUSIBLE_JUMP_KM = 5000


def _clean(value: object) -> str | None:
    """Normalize a cell to a stripped string, treating blanks/NaN as None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    return text or None


def _vehicle_lookup(db: Session) -> tuple[dict[str, Vehicle], dict[str, Vehicle]]:
    vehicles = db.scalars(select(Vehicle).where(Vehicle.deleted_at.is_(None))).all()
    by_plate = {v.plate.upper(): v for v in vehicles}
    by_card = {v.fuel_card_number: v for v in vehicles if v.fuel_card_number}
    return by_plate, by_card


def _suspect_reasons(vehicle: Vehicle, liters: Decimal, odometer: int | None) -> list[str]:
    reasons: list[str] = []
    if liters > Decimal(str(vehicle.tank_capacity_l)):
        reasons.append("liters exceed tank capacity")
    if odometer is not None:
        if odometer < vehicle.current_km:
            reasons.append("odometer below last known reading")
        elif odometer - vehicle.current_km > IMPLAUSIBLE_JUMP_KM:
            reasons.append("implausible odometer jump")
    return reasons


def _parse_row(
    row: dict, by_plate: dict[str, Vehicle], by_card: dict[str, Vehicle]
) -> FuelTransaction:
    """Build a FuelTransaction from a raw row, or raise ValueError to reject it."""
    plate = _clean(row.get("plate"))
    card = _clean(row.get("fuel_card"))
    vehicle = (by_plate.get(plate.upper()) if plate else None) or (
        by_card.get(card) if card else None
    )
    if vehicle is None:
        raise ValueError("unknown vehicle (no matching plate or fuel card)")

    date_raw = _clean(row.get("date"))
    if not date_raw:
        raise ValueError("missing date")
    occurred_at = pd.to_datetime(date_raw, errors="coerce", dayfirst=False)
    if pd.isna(occurred_at):
        raise ValueError(f"unparseable date: {date_raw!r}")

    liters_raw = _clean(row.get("liters"))
    try:
        liters = Decimal(liters_raw) if liters_raw is not None else None
    except (InvalidOperation, TypeError):
        liters = None
    if liters is None or liters <= 0:
        raise ValueError(f"invalid liters: {liters_raw!r}")

    price_raw = _clean(row.get("price"))
    try:
        price = Decimal(price_raw) if price_raw is not None else None
    except (InvalidOperation, TypeError):
        price = None

    odo_raw = _clean(row.get("odometer"))
    odometer = int(float(odo_raw)) if odo_raw is not None else None

    reasons = _suspect_reasons(vehicle, liters, odometer)
    return FuelTransaction(
        vehicle_id=vehicle.id,
        occurred_at=occurred_at.to_pydatetime(),
        liters=liters,
        price=price,
        odometer_reported=odometer,
        station=_clean(row.get("station")),
        is_suspect=bool(reasons),
        suspect_reason="; ".join(reasons) or None,
    )


def _read_dataframe(file_path: str) -> pd.DataFrame:
    if file_path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path, dtype=str)
    return pd.read_csv(file_path, dtype=str)


def process_import(db: Session, batch_id: int, file_path: str) -> ImportBatch:
    """Parse a fuel file and record results on the batch. Atomic commit."""
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise ValueError(f"import batch {batch_id} not found")

    batch.status = ImportStatus.processing
    db.commit()

    try:
        df = _read_dataframe(file_path)
        by_plate, by_card = _vehicle_lookup(db)

        transactions: list[FuelTransaction] = []
        errors: list[dict] = []
        for idx, raw in enumerate(df.to_dict(orient="records"), start=1):
            try:
                txn = _parse_row(raw, by_plate, by_card)
                txn.import_batch_id = batch.id
                transactions.append(txn)
            except ValueError as exc:
                errors.append({"row": idx, "error": str(exc), "data": raw})

        db.add_all(transactions)
        batch.total_rows = len(df)
        batch.imported_rows = len(transactions)
        batch.rejected_rows = len(errors)
        batch.error_report = errors
        batch.status = ImportStatus.completed
        db.commit()  # valid rows + batch summary commit together
    except Exception as exc:  # noqa: BLE001 — record failure, never leave partial data
        db.rollback()
        batch = db.get(ImportBatch, batch_id)
        batch.status = ImportStatus.failed
        batch.error_report = {"fatal": str(exc)}
        db.commit()
        raise

    db.refresh(batch)
    return batch


def run_import_in_background(batch_id: int, file_path: str) -> None:
    """Entry point for BackgroundTasks — owns its own DB session."""
    db = SessionLocal()
    try:
        process_import(db, batch_id, file_path)
    except Exception:  # noqa: BLE001 — status already persisted as 'failed'
        pass
    finally:
        db.close()
