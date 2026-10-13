from datetime import datetime

from pydantic import BaseModel


class ApplicationBase(BaseModel):
    full_name: str
    dob: datetime
    id_number: str
    gender: str
    birth_town: str
    nickname: str | None = None
    country: str
    phone: str
    country_code: str
    business_type: str | None = None
    business_location: str | None = None
    nearest_lodge: str


class ApplicationCreate(BaseModel):
    full_name: str
    dob: datetime
    id_number: str
    gender: str
    birth_town: str
    nickname: str | None = None
    country: str
    phone: str
    country_code: str
    business_type: str | None = None
    business_location: str | None = None
    nearest_lodge: str


class ApplicationUpdate(BaseModel):
    full_name: str | None = None
    dob: datetime | None = None
    id_number: str | None = None
    gender: str | None = None
    birth_town: str | None = None
    nickname: str | None = None
    country: str | None = None
    phone: str | None = None
    country_code: str | None = None
    business_type: str | None = None
    business_location: str | None = None
    nearest_lodge: str | None = None
    status: str | None = None
    review_notes: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    dob: datetime
    id_number: str
    gender: str
    birth_town: str
    nickname: str | None
    country: str
    phone: str
    country_code: str
    business_type: str | None
    business_location: str | None
    nearest_lodge: str
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_notes: str | None
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
    reviewed_at: datetime | None

    class Config:
        from_attributes = True
