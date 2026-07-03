from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import admin_only, get_current_user, get_db, manager_or_admin
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead, DocumentUpdate
from app.services.document import crud

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(
    vehicle_id: int | None = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.list(db, vehicle_id=vehicle_id, include_deleted=include_deleted)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.get(db, document_id)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return crud.create(db, data.model_dump())


@router.patch("/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return crud.update(db, document_id, data.model_dump(exclude_unset=True))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> None:
    crud.soft_delete(db, document_id)


@router.delete("/{document_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    crud.hard_delete(db, document_id)
