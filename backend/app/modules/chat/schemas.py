from datetime import datetime

from pydantic import BaseModel

from app.core.models import MediaTypeEnum, MessageStatusEnum


class ChatBase(BaseModel):
    subject: str | None = None


class ChatCreate(BaseModel):
    member_id: str
    subject: str | None = None


class ChatUpdate(BaseModel):
    subject: str | None = None
    is_archived: bool | None = None


class MessageBase(BaseModel):
    content: str | None = None
    media_url: str | None = None
    media_type: MediaTypeEnum | None = None
    reply_to_id: str | None = None


class MessageCreate(BaseModel):
    content: str | None = None
    media_url: str | None = None
    media_type: MediaTypeEnum | None = None
    reply_to_id: str | None = None


class MessageUpdate(BaseModel):
    content: str | None = None
    is_deleted: bool | None = None
    deleted_for: list[str] | None = None


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    content: str | None
    media_url: str | None
    media_type: MediaTypeEnum | None
    reply_to_id: str | None
    status: MessageStatusEnum
    is_deleted: bool
    deleted_for: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    id: str
    lodge_id: str
    member_id: str
    admin_id: str | None
    subject: str | None
    last_message_at: datetime | None
    last_message_preview: str | None
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
    last_message: str | None
    last_message_at: datetime | None
    unread_count: int
    is_unread: bool
    member_avatar: str | None
