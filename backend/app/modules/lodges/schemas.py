from datetime import datetime

from pydantic import BaseModel


class LodgeBase(BaseModel):
    name: str
    code: str
    country: str
    currency: str = "KES"
    timezone: str = "Africa/Nairobi"


class LodgeCreate(LodgeBase):
    settings: dict = {}


class LodgeUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    country: str | None = None
    currency: str | None = None
    timezone: str | None = None
    settings: dict | None = None


class LodgeResponse(BaseModel):
    id: str
    name: str
    code: str
    country: str
    currency: str
    timezone: str
    settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LodgeListResponse(BaseModel):
    id: str
    name: str
    code: str
    country: str
    currency: str
    user_count: int
    created_at: datetime

    class Config:
        from_attributes = True
