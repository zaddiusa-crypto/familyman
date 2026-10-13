from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.core.models import RoleEnum


class AnnouncementBase(BaseModel):
    title: str
    content: str
    media_urls: List[str] = []
    target_roles: List[str] = ["member"]
    is_published: bool = True
    expires_at: Optional[datetime] = None


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(AnnouncementBase):
    title: Optional[str] = None
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    is_published: Optional[bool] = None
    expires_at: Optional[datetime] = None


class AnnouncementResponse(BaseModel):
    id: str
    lodge_id: str
    author_id: str
    title: str
    content: str
    media_urls: List[str]
    target_roles: List[str]
    is_published: bool
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    id: str
    title: str
    content: str
    media_urls: List[str]
    target_roles: List[str]
    is_published: bool
    published_at: Optional[datetime]
    author_name: str
    created_at: datetime

    class Config:
        from_attributes = True