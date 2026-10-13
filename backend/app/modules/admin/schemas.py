from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class BroadcastCreate(BaseModel):
    title: str
    body: str
    data: dict = {}
    target_roles: List[str] = ["member"]
    priority: str = "normal"
    scheduled_at: Optional[datetime] = None


class BroadcastResponse(BaseModel):
    id: str
    title: str
    body: str
    data: dict
    target_roles: List[str]
    priority: str
    status: str
    sent_count: int
    failed_count: int
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    total_users: int
    total_applications: int
    pending_applications: int
    total_chats: int
    total_messages: int
    unread_chats: int
    total_payments: int
    pending_payments: int
    revenue: float
    active_users_24h: int
    active_users_7d: int
    fcm_tokens_count: int
    sync_queue_depth: int