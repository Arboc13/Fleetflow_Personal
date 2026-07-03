import datetime as dt
from typing import Generic, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Base
from app.services.vehicle import get_vehicle

ModelT = TypeVar("ModelT", bound=Base)


class VehicleChildCRUD(Generic[ModelT]):
    """Reusable CRUD for records that belong to a vehicle and are soft-deletable.

    Used by documents, service records, and maintenance rules — same shape,
    same RBAC/soft-delete policy. Vehicle existence is checked on create.
    """

    def __init__(self, model: type[ModelT], not_found: str) -> None:
        self.model = model
        self.not_found = not_found

    def list(
        self,
        db: Session,
        *,
        vehicle_id: int | None = None,
        include_deleted: bool = False,
    ) -> list[ModelT]:
        stmt = select(self.model)
        if vehicle_id is not None:
            stmt = stmt.where(self.model.vehicle_id == vehicle_id)
        if not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
        return list(db.scalars(stmt.order_by(self.model.id)))

    def get(self, db: Session, obj_id: int, *, include_deleted: bool = False) -> ModelT:
        obj = db.get(self.model, obj_id)
        if obj is None or (obj.deleted_at is not None and not include_deleted):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=self.not_found)
        return obj

    def create(self, db: Session, data: dict) -> ModelT:
        get_vehicle(db, data["vehicle_id"])  # 404 if the vehicle is missing/deleted
        obj = self.model(**data)
        db.add(obj)
        self._commit(db)
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj_id: int, changes: dict) -> ModelT:
        obj = self.get(db, obj_id)
        for field, value in changes.items():
            setattr(obj, field, value)
        self._commit(db)
        db.refresh(obj)
        return obj

    def soft_delete(self, db: Session, obj_id: int) -> None:
        obj = self.get(db, obj_id)
        obj.deleted_at = dt.datetime.now(dt.timezone.utc)
        db.commit()

    def hard_delete(self, db: Session, obj_id: int) -> None:
        obj = self.get(db, obj_id, include_deleted=True)
        db.delete(obj)
        db.commit()

    @staticmethod
    def _commit(db: Session) -> None:
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value violates a database constraint (check dates/amounts).",
            ) from exc
