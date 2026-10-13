from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.models import RoleEnum, UserStatusEnum


class UserListResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    role: RoleEnum
    status: UserStatusEnum
    language: str
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    country_code: Optional[str]
    role: RoleEnum
    status: UserStatusEnum
    language: str
    fcm_tokens: List[str]
    telegram_chat_id: Optional[str]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None
    language: Optional[str] = None
    status: Optional[UserStatusEnum] = None
    role: Optional[str] = None


class UserStatsResponse(BaseModel):
    total: int
    approved: int
    pending: int
    rejected: int
    suspended: int