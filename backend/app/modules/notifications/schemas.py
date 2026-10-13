from datetime import datetime

from pydantic import BaseModel

from app.core.models import NotificationPriorityEnum


class NotificationBase(BaseModel):
    type: str
    title: str
    body: str
    data: dict = {}
    priority: NotificationPriorityEnum = "normal"


class NotificationCreate(NotificationBase):
    user_id: str
    target_roles: list[str] | None = None


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str
    data: dict
    priority: NotificationPriorityEnum
    is_read: bool
    read_at: datetime | None
    sent_via: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: bool | None = None


class NotificationListResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    limit: int
