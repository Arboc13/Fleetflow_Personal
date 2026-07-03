import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db, manager_or_admin
from app.models.fuel import FuelTransaction, ImportBatch, ImportStatus
from app.models.user import User
from app.schemas.fuel import FuelTransactionRead, ImportBatchRead
from app.services.fuel_import import run_import_in_background

router = APIRouter(tags=["fuel-imports"])

ALLOWED_EXT = (".csv", ".xlsx", ".xls")


@router.post(
    "/fuel-imports", response_model=ImportBatchRead, status_code=status.HTTP_202_ACCEPTED
)
def upload_fuel_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(manager_or_admin),
) -> ImportBatch:
    filename = file.filename or "upload"
    if not filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXT)}",
        )

    batch = ImportBatch(
        filename=filename, status=ImportStatus.pending, uploaded_by=user.id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"batch_{batch.id}_{filename}"
    with stored_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # Parse off the request thread; the client polls GET /fuel-imports/{id}.
    background_tasks.add_task(run_import_in_background, batch.id, str(stored_path))
    return batch


@router.get("/fuel-imports", response_model=list[ImportBatchRead])
def list_batches(
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return list(db.scalars(select(ImportBatch).order_by(ImportBatch.id.desc())))


@router.get("/fuel-imports/{batch_id}", response_model=ImportBatchRead)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return batch


@router.get("/fuel-transactions", response_model=list[FuelTransactionRead])
def list_transactions(
    vehicle_id: int | None = None,
    batch_id: int | None = None,
    suspect_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(FuelTransaction)
    if vehicle_id is not None:
        stmt = stmt.where(FuelTransaction.vehicle_id == vehicle_id)
    if batch_id is not None:
        stmt = stmt.where(FuelTransaction.import_batch_id == batch_id)
    if suspect_only:
        stmt = stmt.where(FuelTransaction.is_suspect.is_(True))
    return list(db.scalars(stmt.order_by(FuelTransaction.id)))
