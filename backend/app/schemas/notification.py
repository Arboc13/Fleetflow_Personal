import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.models.notification import Severity


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    severity: Severity
    message: str
    entity_type: str | None
    entity_id: int | None
    read_at: dt.datetime | None
    created_at: dt.datetime


class UnreadCount(BaseModel):
    unread: int
