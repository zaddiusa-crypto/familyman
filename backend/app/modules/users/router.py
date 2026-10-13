from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.modules.users.schemas import (
    UserListResponse, UserDetailResponse, UserUpdateRequest, UserStatsResponse
)
from app.modules.auth.dependencies import get_db, get_current_user, get_current_active_user
from app.core.models import User, RoleEnum, UserStatusEnum
from app.core.rbac import require_permission, require_role
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundError, ValidationError


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(require_permission("admin.users.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.count(User.id).label("total"),
            func.count(User.id).filter(User.status == UserStatusEnum.APPROVED).label("approved"),
            func.count(User.id).filter(User.status == UserStatusEnum.PENDING).label("pending"),
            func.count(User.id).filter(User.status == UserStatusEnum.REJECTED).label("rejected"),
            func.count(User.id).filter(User.status == UserStatusEnum.SUSPENDED).label("suspended"),
        ).where(User.lodge_id == current_user.lodge_id)
    )
    row = result.one()
    return UserStatsResponse(
        total=row.total, approved=row.approved, pending=row.pending,
        rejected=row.rejected, suspended=row.suspended
    )


@router.get("", response_model=List[dict])
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).where(User.lodge_id == current_user.lodge_id)

    if search:
        query = query.where(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.where(User.status == status)

    if role:
        query = query.where(User.role == role)

    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    query = query.order_by(User.created_at.desc()).offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "phone": u.phone,
                "role": u.role.value,
                "status": u.status.value,
                "language": u.language,
                "created_at": u.created_at.isoformat(),
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": 1,
        "limit": 20,
    }


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "country_code": current_user.country_code,
        "role": current_user.role.value,
        "status": current_user.status.value,
        "language": current_user.language,
        "fcm_tokens": current_user.fcm_tokens,
        "telegram_chat_id": current_user.telegram_chat_id,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "created_at": current_user.created_at.isoformat(),
        "updated_at": current_user.updated_at.isoformat(),
    }


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from app.core.models import User

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.lodge_id == current_user.lodge_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "country_code": user.country_code,
        "role": user.role.value,
        "status": user.status.value,
        "language": user.language,
        "fcm_tokens": user.fcm_tokens,
        "telegram_chat_id": user.telegram_chat_id,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@router.patch("/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from app.core.models import User, RoleEnum, UserStatusEnum
    from app.core.security import get_password_hash

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.lodge_id == current_user.lodge_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "password" in data:
        from app.core.security import get_password_hash
        data["password_hash"] = get_password_hash(data.pop("password"))

    for key, value in data.items():
        if hasattr(user, key) and value is not None:
            if key == "role":
                try:
                    value = RoleEnum(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid role")
            elif key == "status":
                try:
                    value = UserStatusEnum(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid status")
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return {"message": "User updated successfully"}


@router.post("/{user_id}/fcm-token")
async def add_fcm_token(
    user_id: str,
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from app.core.models import User

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.lodge_id == current_user.lodge_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if token not in user.fcm_tokens:
        user.fcm_tokens = list(set(user.fcm_tokens + [token]))
        await db.commit()

    return {"message": "FCM token added"}


@router.delete("/{user_id}/fcm-token")
async def remove_fcm_token(
    user_id: str,
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from app.core.models import User

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.lodge_id == current_user.lodge_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if token in user.fcm_tokens:
        user.fcm_tokens.remove(token)
        await db.commit()

    return {"message": "FCM token removed"}