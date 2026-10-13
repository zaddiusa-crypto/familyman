from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.modules.applications.schemas import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, ApplicationListResponse
)
from app.modules.auth.dependencies import get_db, get_current_user, get_current_active_user
from app.core.models import Application, ApplicationStatusEnum, User, UserStatusEnum, RoleEnum, FeeSchedule
from app.core.rbac import require_permission, require_role
from app.core.exceptions import NotFoundError, ValidationError


router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    application = Application(
        lodge_id=current_user.lodge_id,
        user_id=current_user.id,
        full_name=data["full_name"],
        dob=data["dob"],
        id_number=data["id_number"],
        gender=data["gender"],
        birth_town=data["birth_town"],
        nickname=data.get("nickname"),
        country=data["country"],
        phone=data["phone"],
        country_code=data.get("country_code"),
        business_type=data.get("business_type"),
        business_location=data.get("business_location"),
        nearest_lodge=data["nearest_lodge"],
        status=ApplicationStatusEnum.PENDING,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    return {"message": "Application submitted successfully", "application_id": str(application.id)}


@router.get("", response_model=dict)
async def list_applications(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Application).where(Application.lodge_id == current_user.lodge_id)

    if current_user.role.value == "member":
        query = query.where(Application.user_id == current_user.id)
    elif current_user.role.value == "lodge_admin":
        pass  # Can see all applications in their lodge

    if status:
        query = query.where(Application.status == status)

    if search:
        from sqlalchemy import or_
        query = query.where(
            or_(
                Application.full_name.ilike(f"%{search}%"),
                Application.id_number.ilike(f"%{search}%"),
                Application.email.ilike(f"%{search}%"),
            )
        )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Application.submitted_at.desc()).offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    applications = result.scalars().all()

    # Get user info for each application
    user_ids = [app.user_id for app in applications]
    users_result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users_map = {u.id: u for u in users_result.scalars().all()}

    items = []
    for app in applications:
        user = users_map.get(app.user_id)
        items.append({
            "id": str(app.id),
            "full_name": app.full_name,
            "email": users_map.get(app.user_id).email if users_map.get(app.user_id) else None,
            "phone": app.phone,
            "status": app.status.value,
            "submitted_at": app.submitted_at.isoformat(),
            "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
        })

    return {"items": items, "total": 0, "page": 1, "limit": 20}


@router.get("/fees", response_model=List[dict])
async def get_fee_schedule(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.models import FeeSchedule
    from sqlalchemy import select

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
        }
        for f in fees
    ]


@router.get("/{application_id}", response_model=dict)
async def get_application(
    application_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select
    from app.core.models import Application, User

    result = await db.execute(
        select(Application).where(
            Application.id == UUID(application_id),
            Application.lodge_id == current_user.lodge_id
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check permissions
    if current_user.role.value == "member" and application.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    user_result = await db.execute(select(User).where(User.id == application.user_id))
    user = user_result.scalar_one_or_none()

    return {
        "id": str(application.id),
        "user_id": str(application.user_id),
        "full_name": application.full_name,
        "dob": application.dob.isoformat(),
        "id_number": application.id_number,
        "gender": application.gender,
        "birth_town": application.birth_town,
        "nickname": application.nickname,
        "country": application.country,
        "phone": application.phone,
        "country_code": application.country_code,
        "business_type": application.business_type,
        "business_location": application.business_location,
        "nearest_lodge": application.nearest_lodge,
        "status": application.status.value,
        "reviewed_by": str(application.reviewed_by) if application.reviewed_by else None,
        "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None,
        "review_notes": application.review_notes,
        "submitted_at": application.submitted_at.isoformat(),
        "created_at": application.created_at.isoformat(),
        "updated_at": application.updated_at.isoformat(),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
        } if user else None,
    }


@router.patch("/{application_id}", response_model=dict)
async def update_application(
    application_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select
    from app.core.models import Application, ApplicationStatusEnum

    result = await db.execute(
        select(Application).where(
            Application.id == UUID(application_id),
            Application.lodge_id == current_user.lodge_id
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role.value == "member":
        if application.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if application.status != ApplicationStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Cannot update non-pending application")
        allowed_fields = ["full_name", "dob", "id_number", "gender", "birth_town", "nickname",
                         "country", "phone", "country_code", "business_type", "business_location", "nearest_lodge"]
    else:
        allowed_fields = ["status", "review_notes", "full_name", "dob", "id_number", "gender",
                         "birth_town", "nickname", "country", "phone", "country_code",
                         "business_type", "business_location", "nearest_lodge"]

    for key, value in data.items():
        if key in allowed_fields and value is not None:
            if key == "status":
                try:
                    from app.core.models import ApplicationStatusEnum
                    value = ApplicationStatusEnum(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid status")
            if key == "status" and value == ApplicationStatusEnum.APPROVED:
                application.reviewed_by = current_user.id
                application.reviewed_at = datetime.now(timezone.utc)
            setattr(application, key, value)

    await db.commit()
    await db.refresh(application)

    return {"message": "Application updated successfully"}


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: str,
    status: str,
    review_notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select
    from app.core.models import Application, ApplicationStatusEnum, User

    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(Application).where(
            Application.id == UUID(application_id),
            Application.lodge_id == current_user.lodge_id
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    try:
        new_status = ApplicationStatusEnum(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    application.status = ApplicationStatusEnum(status)
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.now(timezone.utc)
    if review_notes:
        application.review_notes = review_notes

    await db.commit()

    return {"message": f"Application status updated to {status.value}"}