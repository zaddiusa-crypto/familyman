from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.modules.payments.schemas import PaymentCreate, PaymentUpdate, PaymentResponse
from app.modules.auth.dependencies import get_db, get_current_user, get_current_active_user
from app.core.models import Payment, FeeSchedule, PaymentStatusEnum, User
from app.core.rbac import require_permission
from app.core.exceptions import NotFoundError


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/fees", response_model=List[dict])
async def list_fee_schedules(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FeeSchedule).where(
            FeeSchedule.lodge_id == current_user.lodge_id,
            FeeSchedule.is_active == True
        ).order_by(FeeSchedule.sort_order)
    )
    fees = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "name": f.name,
            "label": f.label,
            "description": f.description,
            "amount": float(f.amount),
            "currency": f.currency,
            "is_required": f.is_required,
            "is_active": f.is_active,
            "sort_order": f.sort_order,
        }
        for f in fees
    ]


@router.post("/fees", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_fee_schedule(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    fee = FeeSchedule(
        lodge_id=current_user.lodge_id,
        name=data["name"],
        label=data["label"],
        description=data.get("description"),
        amount=data["amount"],
        currency=data["currency"],
        is_required=data.get("is_required", False),
        sort_order=data.get("sort_order", 0),
        is_active=data.get("is_active", True),
    )
    db.add(fee)
    await db.commit()
    await db.refresh(fee)

    return {"message": "Fee schedule created", "fee_id": str(fee.id)}


@router.patch("/fees/{fee_id}")
async def update_fee_schedule(
    fee_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select

    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(FeeSchedule).where(
            FeeSchedule.id == UUID(fee_id),
            FeeSchedule.lodge_id == current_user.lodge_id
        )
    )
    fee = result.scalar_one_or_none()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee schedule not found")

    for key, value in data.items():
        if hasattr(fee, key) and value is not None:
            setattr(fee, key, value)

    await db.commit()
    return {"message": "Fee schedule updated"}


@router.delete("/fees/{fee_id}")
async def delete_fee_schedule(
    fee_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select

    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(FeeSchedule).where(
            FeeSchedule.id == UUID(fee_id),
            FeeSchedule.lodge_id == current_user.lodge_id
        )
    )
    fee = result.scalar_one_or_none()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee schedule not found")

    await db.delete(fee)
    await db.commit()
    return {"message": "Fee schedule deleted"}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def record_payment(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    payment = Payment(
        lodge_id=current_user.lodge_id,
        user_id=current_user.id,
        fee_schedule_id=UUID(data["fee_schedule_id"]) if data.get("fee_schedule_id") else None,
        amount=data["amount"],
        currency=data["currency"],
        method=data.get("method"),
        reference=data.get("reference"),
        status=PaymentStatusEnum.PENDING,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return {"message": "Payment recorded", "payment_id": str(payment.id)}


@router.get("", response_model=dict)
async def list_payments(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Payment).where(Payment.lodge_id == current_user.lodge_id)

    if current_user.role.value == "member":
        query = query.where(Payment.user_id == current_user.id)

    if status:
        query = query.where(Payment.status == status)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Payment.created_at.desc()).offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    payments = result.scalars().all()

    return {
        "items": [
            {
                "id": str(p.id),
                "user_id": str(p.user_id),
                "fee_schedule_id": str(p.fee_schedule_id) if p.fee_schedule_id else None,
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status.value,
                "method": p.method,
                "reference": p.reference,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{payment_id}", response_model=dict)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select

    result = await db.execute(
        select(Payment).where(
            Payment.id == UUID(payment_id),
            Payment.lodge_id == current_user.lodge_id
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if current_user.role.value == "member" and payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "id": str(payment.id),
        "user_id": str(payment.user_id),
        "fee_schedule_id": str(payment.fee_schedule_id) if payment.fee_schedule_id else None,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "status": payment.status.value,
        "method": payment.method,
        "reference": payment.reference,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "created_at": payment.created_at.isoformat(),
    }


@router.patch("/{payment_id}")
async def update_payment(
    payment_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select

    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(Payment).where(
            Payment.id == UUID(payment_id),
            Payment.lodge_id == current_user.lodge_id
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    for key, value in data.items():
        if hasattr(payment, key) and value is not None:
            if key == "status":
                from app.core.models import PaymentStatusEnum
                try:
                    value = PaymentStatusEnum(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid status")
                if value == PaymentStatusEnum.COMPLETED and not payment.paid_at:
                    from datetime import datetime, timezone
                    value = datetime.now(timezone.utc)
            setattr(payment, key, value)

    await db.commit()
    return {"message": "Payment updated"}