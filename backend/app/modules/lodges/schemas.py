from typing import Optional, List
from uuid import UUID
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
    name: Optional[str] = None
    code: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    settings: Optional[dict] = None


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