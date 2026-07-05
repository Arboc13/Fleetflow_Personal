import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


def list_for_user(db: Session, user: User, *, unread_only: bool = False) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return list(db.scalars(stmt.order_by(Notification.created_at.desc(), Notification.id.desc())))


def unread_count(db: Session, user: User) -> int:
    return db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id, Notification.read_at.is_(None)
        )
    ) or 0


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    note = db.get(Notification, notification_id)
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if note.read_at is None:
        note.read_at = dt.datetime.now(dt.timezone.utc)
        db.commit()
        db.refresh(note)
    return note


def mark_all_read(db: Session, user: User) -> int:
    notes = db.scalars(
        select(Notification).where(
            Notification.user_id == user.id, Notification.read_at.is_(None)
        )
    ).all()
    now = dt.datetime.now(dt.timezone.utc)
    for note in notes:
        note.read_at = now
    db.commit()
    return len(notes)
