import datetime as dt

from pydantic import BaseModel


class VehicleTCORow(BaseModel):
    vehicle_id: int
    plate: str
    make: str
    model: str
    fuel_cost: float
    service_cost: float
    document_cost: float
    total_cost: float
    km_driven: int
    cost_per_km: float | None  # None when no km were driven in the period
    utilization_pct: float


class FleetTotals(BaseModel):
    fuel_cost: float
    service_cost: float
    document_cost: float
    total_cost: float
    km_driven: int
    cost_per_km: float | None
    utilization_pct: float


class TCOReport(BaseModel):
    date_from: dt.date
    date_to: dt.date
    rows: list[VehicleTCORow]
    fleet: FleetTotals
