from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_change(
    db: Session,
    *,
    entity: str,
    entity_id: int,
    field: str,
    old_value: object,
    new_value: object,
    user_id: int | None,
) -> None:
    """Append an audit row. Caller commits within its own transaction."""
    db.add(
        AuditLog(
            entity=entity,
            entity_id=entity_id,
            field=field,
            old_value=None if old_value is None else str(old_value),
            new_value=None if new_value is None else str(new_value),
            user_id=user_id,
        )
    )
