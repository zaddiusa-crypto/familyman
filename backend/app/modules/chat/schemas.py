from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.core.models import MessageStatusEnum, MediaTypeEnum


class ChatBase(BaseModel):
    subject: Optional[str] = None


class ChatCreate(BaseModel):
    member_id: str
    subject: Optional[str] = None


class ChatUpdate(BaseModel):
    subject: Optional[str] = None
    is_archived: Optional[bool] = None


class MessageBase(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[MediaTypeEnum] = None
    reply_to_id: Optional[str] = None


class MessageCreate(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[MediaTypeEnum] = None
    reply_to_id: Optional[str] = None


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_deleted: Optional[bool] = None
    deleted_for: Optional[List[str]] = None


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    content: Optional[str]
    media_url: Optional[str]
    media_type: Optional[MediaTypeEnum]
    reply_to_id: Optional[str]
    status: MessageStatusEnum
    is_deleted: bool
    deleted_for: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    id: str
    lodge_id: str
    member_id: str
    admin_id: Optional[str]
    subject: Optional[str]
    last_message_at: Optional[datetime]
    last_message_preview: Optional[str]
    unread_admin: int
    unread_member: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatListResponse(BaseModel):
    id: str
    member_name: str
    member_phone: str
    member_country: str
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    unread_count: int
    is_unread: bool
    member_avatar: Optional[str]