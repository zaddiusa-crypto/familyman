from datetime import datetime

from pydantic import BaseModel

from app.core.models import RoleEnum, UserStatusEnum


class UserListResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None
    role: RoleEnum
    status: UserStatusEnum
    language: str
    created_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None
    country_code: str | None
    role: RoleEnum
    status: UserStatusEnum
    language: str
    fcm_tokens: list[str]
    telegram_chat_id: str | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    country_code: str | None = None
    language: str | None = None
    status: UserStatusEnum | None = None
    role: str | None = None


class UserStatsResponse(BaseModel):
    total: int
    approved: int
    pending: int
    rejected: int
    suspended: int
