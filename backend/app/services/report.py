"""TCO + utilization report (F-601).

cost_per_km = (fuel + service + document costs in period) / km driven in
period (closed trip sheets). Utilization = share of the period each vehicle
was covered by an allocation. All sums run as SQL aggregates; only the
allocation interval clipping happens in Python.
"""
import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.document import VehicleDocument
from app.models.fuel import FuelTransaction
from app.models.service import ServiceRecord
from app.models.trip_sheet import TripSheet, TripStatus
from app.models.vehicle import Vehicle
from app.schemas.report import FleetTotals, TCOReport, VehicleTCORow
from app.services.vehicle import get_vehicle


def _as_utc(value: dt.datetime) -> dt.datetime:
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def _sum_by_vehicle(db: Session, stmt) -> dict[int, float]:
    return {vid: float(total or 0) for vid, total in db.execute(stmt)}


def _allocated_days(
    allocs: list[Allocation], start: dt.datetime, end: dt.datetime
) -> float:
    """Days of [start, end) covered by the given (non-overlapping) allocations."""
    covered = dt.timedelta()
    for a in allocs:
        a_start = _as_utc(a.start_at)
        a_end = _as_utc(a.end_at) if a.end_at is not None else end
        clip_start = max(a_start, start)
        clip_end = min(a_end, end)
        if clip_end > clip_start:
            covered += clip_end - clip_start
    return covered.total_seconds() / 86400


def tco_report(
    db: Session,
    *,
    date_from: dt.date,
    date_to: dt.date,
    vehicle_id: int | None = None,
) -> TCOReport:
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_to must not be before date_from.",
        )
    # [start, end) — date_to is inclusive.
    start = dt.datetime.combine(date_from, dt.time.min, tzinfo=dt.timezone.utc)
    end = dt.datetime.combine(
        date_to + dt.timedelta(days=1), dt.time.min, tzinfo=dt.timezone.utc
    )
    period_days = (end - start).total_seconds() / 86400

    if vehicle_id is not None:
        vehicles = [get_vehicle(db, vehicle_id)]
    else:
        vehicles = list(
            db.scalars(
                select(Vehicle).where(Vehicle.deleted_at.is_(None)).order_by(Vehicle.id)
            )
        )
    vehicle_ids = [v.id for v in vehicles]

    # price is the per-liter price, so cost = liters * price.
    fuel = _sum_by_vehicle(
        db,
        select(
            FuelTransaction.vehicle_id,
            func.sum(FuelTransaction.liters * FuelTransaction.price),
        )
        .where(
            FuelTransaction.vehicle_id.in_(vehicle_ids),
            FuelTransaction.price.is_not(None),
            FuelTransaction.occurred_at >= start,
            FuelTransaction.occurred_at < end,
        )
        .group_by(FuelTransaction.vehicle_id),
    )
    service = _sum_by_vehicle(
        db,
        select(ServiceRecord.vehicle_id, func.sum(ServiceRecord.cost))
        .where(
            ServiceRecord.vehicle_id.in_(vehicle_ids),
            ServiceRecord.deleted_at.is_(None),
            ServiceRecord.date >= date_from,
            ServiceRecord.date <= date_to,
        )
        .group_by(ServiceRecord.vehicle_id),
    )
    # Document costs count in the period the document was issued (bought).
    documents = _sum_by_vehicle(
        db,
        select(VehicleDocument.vehicle_id, func.sum(VehicleDocument.cost))
        .where(
            VehicleDocument.vehicle_id.in_(vehicle_ids),
            VehicleDocument.deleted_at.is_(None),
            VehicleDocument.issue_date >= date_from,
            VehicleDocument.issue_date <= date_to,
        )
        .group_by(VehicleDocument.vehicle_id),
    )
    km = _sum_by_vehicle(
        db,
        select(TripSheet.vehicle_id, func.sum(TripSheet.end_km - TripSheet.start_km))
        .where(
            TripSheet.vehicle_id.in_(vehicle_ids),
            TripSheet.status == TripStatus.closed,
            TripSheet.deleted_at.is_(None),
            TripSheet.departure_at >= start,
            TripSheet.departure_at < end,
        )
        .group_by(TripSheet.vehicle_id),
    )
    allocations = list(
        db.scalars(
            select(Allocation).where(
                Allocation.deleted_at.is_(None),
                Allocation.vehicle_id.in_(vehicle_ids),
                Allocation.start_at < end,
                or_(Allocation.end_at.is_(None), Allocation.end_at > start),
            )
        )
    )
    allocs_by_vehicle: dict[int, list[Allocation]] = {}
    for a in allocations:
        allocs_by_vehicle.setdefault(a.vehicle_id, []).append(a)

    rows: list[VehicleTCORow] = []
    for v in vehicles:
        fuel_cost = round(fuel.get(v.id, 0.0), 2)
        service_cost = round(service.get(v.id, 0.0), 2)
        document_cost = round(documents.get(v.id, 0.0), 2)
        total_cost = round(fuel_cost + service_cost + document_cost, 2)
        km_driven = int(km.get(v.id, 0))
        allocated = _allocated_days(allocs_by_vehicle.get(v.id, []), start, end)
        rows.append(
            VehicleTCORow(
                vehicle_id=v.id,
                plate=v.plate,
                make=v.make,
                model=v.model,
                fuel_cost=fuel_cost,
                service_cost=service_cost,
                document_cost=document_cost,
                total_cost=total_cost,
                km_driven=km_driven,
                cost_per_km=round(total_cost / km_driven, 3) if km_driven else None,
                utilization_pct=round(min(100.0, allocated / period_days * 100), 1),
            )
        )

    fleet_total = round(sum(r.total_cost for r in rows), 2)
    fleet_km = sum(r.km_driven for r in rows)
    fleet = FleetTotals(
        fuel_cost=round(sum(r.fuel_cost for r in rows), 2),
        service_cost=round(sum(r.service_cost for r in rows), 2),
        document_cost=round(sum(r.document_cost for r in rows), 2),
        total_cost=fleet_total,
        km_driven=fleet_km,
        cost_per_km=round(fleet_total / fleet_km, 3) if fleet_km else None,
        utilization_pct=(
            round(sum(r.utilization_pct for r in rows) / len(rows), 1) if rows else 0.0
        ),
    )
    return TCOReport(date_from=date_from, date_to=date_to, rows=rows, fleet=fleet)
