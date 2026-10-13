from typing import Optional, List
from uuid import UUID
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
    target_roles: Optional[List[str]] = None


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str
    data: dict
    priority: NotificationPriorityEnum
    is_read: bool
    read_at: Optional[datetime]
    sent_via: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationListResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    limit: int