from datetime import datetime

from pydantic import BaseModel

from app.core.models import PaymentStatusEnum


class PaymentBase(BaseModel):
    fee_schedule_id: str | None = None
    amount: float
    currency: str
    method: str | None = None
    reference: str | None = None


class PaymentCreate(PaymentBase):
    fee_schedule_id: str


class PaymentUpdate(BaseModel):
    status: PaymentStatusEnum | None = None
    method: str | None = None
    reference: str | None = None
    paid_at: datetime | None = None


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    fee_schedule_id: str | None
    amount: float
    currency: str
    status: PaymentStatusEnum
    method: str | None
    reference: str | None
    paid_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class FeeScheduleResponse(BaseModel):
    id: str
    name: str
    label: str
    description: str | None
    amount: float
    currency: str
    is_required: bool
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True
