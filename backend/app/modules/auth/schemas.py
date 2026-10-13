from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.core.models import RoleEnum, UserStatusEnum


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    country_code: Optional[str] = Field(None, max_length=5)
    language: str = Field("en", max_length=5)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    lodge_code: str = Field(..., max_length=20)
    country: str = Field(..., max_length=2)
    business_type: Optional[str] = None
    business_location: Optional[str] = None
    nearest_lodge: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    country_code: Optional[str] = Field(None, max_length=5)
    language: Optional[str] = Field(None, max_length=5)
    fcm_tokens: Optional[list[str]] = None
    telegram_chat_id: Optional[str] = None


class UserResponse(UserBase):
    id: str
    role: RoleEnum
    status: UserStatusEnum
    lodge_id: str
    fcm_tokens: list[str] = []
    telegram_chat_id: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class RegisterApplicationRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    dob: str
    id_number: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., max_length=10)
    birth_town: str = Field(..., min_length=1, max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)
    country: str = Field(..., max_length=2)
    phone: str = Field(..., min_length=7, max_length=15)
    country_code: str = Field(..., max_length=5)
    business_type: Optional[str] = None
    business_location: Optional[str] = None
    nearest_lodge: str = Field(..., min_length=1, max_length=200)