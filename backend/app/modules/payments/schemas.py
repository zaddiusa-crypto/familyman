from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.core.models import PaymentStatusEnum


class PaymentBase(BaseModel):
    fee_schedule_id: Optional[str] = None
    amount: float
    currency: str
    method: Optional[str] = None
    reference: Optional[str] = None


class PaymentCreate(PaymentBase):
    fee_schedule_id: str


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatusEnum] = None
    method: Optional[str] = None
    reference: Optional[str] = None
    paid_at: Optional[datetime] = None


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    fee_schedule_id: Optional[str]
    amount: float
    currency: str
    status: PaymentStatusEnum
    method: Optional[str]
    reference: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class FeeScheduleResponse(BaseModel):
    id: str
    name: str
    label: str
    description: Optional[str]
    amount: float
    currency: str
    is_required: bool
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True