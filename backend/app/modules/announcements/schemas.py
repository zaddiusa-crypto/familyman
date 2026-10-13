from datetime import datetime

from pydantic import BaseModel


class AnnouncementBase(BaseModel):
    title: str
    content: str
    media_urls: list[str] = []
    target_roles: list[str] = ["member"]
    is_published: bool = True
    expires_at: datetime | None = None


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(AnnouncementBase):
    title: str | None = None
    content: str | None = None
    media_urls: list[str] | None = None
    target_roles: list[str] | None = None
    is_published: bool | None = None
    expires_at: datetime | None = None


class AnnouncementResponse(BaseModel):
    id: str
    lodge_id: str
    author_id: str
    title: str
    content: str
    media_urls: list[str]
    target_roles: list[str]
    is_published: bool
    published_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    id: str
    title: str
    content: str
    media_urls: list[str]
    target_roles: list[str]
    is_published: bool
    published_at: datetime | None
    author_name: str
    created_at: datetime

    class Config:
        from_attributes = True
