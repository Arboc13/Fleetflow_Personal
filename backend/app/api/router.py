from fastapi import APIRouter

from app.api.routes import (
    auth,
    documents,
    drivers,
    fuel_imports,
    maintenance_rules,
    service_records,
    trip_sheets,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(vehicles.router)
api_router.include_router(drivers.router)
api_router.include_router(documents.router)
api_router.include_router(service_records.router)
api_router.include_router(maintenance_rules.router)
api_router.include_router(trip_sheets.router)
api_router.include_router(fuel_imports.router)
