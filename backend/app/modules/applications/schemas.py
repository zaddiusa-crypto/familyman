from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.core.models import ApplicationStatusEnum


class ApplicationBase(BaseModel):
    full_name: str
    dob: datetime
    id_number: str
    gender: str
    birth_town: str
    nickname: Optional[str] = None
    country: str
    phone: str
    country_code: str
    business_type: Optional[str] = None
    business_location: Optional[str] = None
    nearest_lodge: str


class ApplicationCreate(BaseModel):
    full_name: str
    dob: datetime
    id_number: str
    gender: str
    birth_town: str
    nickname: Optional[str] = None
    country: str
    phone: str
    country_code: str
    business_type: Optional[str] = None
    business_location: Optional[str] = None
    nearest_lodge: str


class ApplicationUpdate(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[datetime] = None
    id_number: Optional[str] = None
    gender: Optional[str] = None
    birth_town: Optional[str] = None
    nickname: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None
    business_type: Optional[str] = None
    business_location: Optional[str] = None
    nearest_lodge: Optional[str] = None
    status: Optional[str] = None
    review_notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    dob: datetime
    id_number: str
    gender: str
    birth_town: str
    nickname: Optional[str]
    country: str
    phone: str
    country_code: str
    business_type: Optional[str]
    business_location: Optional[str]
    nearest_lodge: str
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True