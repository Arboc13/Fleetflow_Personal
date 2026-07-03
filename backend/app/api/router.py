from fastapi import APIRouter

from app.api.routes import auth, drivers, vehicles

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(vehicles.router)
api_router.include_router(drivers.router)
