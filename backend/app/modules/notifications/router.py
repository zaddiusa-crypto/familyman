from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.modules.notifications.schemas import NotificationCreate, NotificationResponse
from app.modules.auth.dependencies import get_db, get_current_user, get_current_active_user
from app.core.models import Notification, NotificationPriorityEnum, User
from app.core.rbac import require_permission
from app.core.exceptions import NotFoundError


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=dict)
async def list_notifications(
    page: int = 1,
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == current_user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Notification.created_at.desc()).offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    notifications = result.scalars().all()

    return {
        "items": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "data": n.data,
                "priority": n.priority.value,
                "is_read": n.is_read,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "sent_via": n.sent_via,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.core.models import Notification

    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    )
    count = result.scalar() or 0
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select, update

    result = await db.execute(
        select(Notification).where(
            Notification.id == UUID(notification_id),
            Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"message": "All notifications marked as read"}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    from uuid import UUID
    from app.core.models import User, NotificationPriorityEnum

    target_user_id = UUID(data.user_id)
    target_user_result = await db.execute(
        select(User).where(User.id == UUID(data.user_id), User.lodge_id == current_user.lodge_id)
    )
    target_user = target_user_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    notification = Notification(
        lodge_id=current_user.lodge_id,
        user_id=target_user.id,
        type=data.type,
        title=data.title,
        body=data.body,
        data=data.data or {},
        priority=data.priority,
    )
    db.add(notification)
    await db.commit()

    return {"message": "Notification created", "notification_id": str(notification.id)}


@router.post("/broadcast", response_model=dict)
async def broadcast_notification(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    from app.core.models import User, NotificationPriorityEnum, RoleEnum
    from sqlalchemy import select

    target_roles = data.get("target_roles", ["member"])
    query = select(User).where(User.lodge_id == current_user.lodge_id)
    if target_roles:
        query = query.where(User.role.in_(target_roles))

    result = await db.execute(query)
    users = result.scalars().all()

    notifications = []
    for user in users:
        notification = Notification(
            lodge_id=current_user.lodge_id,
            user_id=user.id,
            type="broadcast",
            title=data["title"],
            body=data["body"],
            data=data.get("data", {}),
            priority=data.get("priority", "normal"),
        )
        notifications.append(notification)

    db.add_all(notifications)
    await db.commit()

    return {"message": f"Broadcast sent to {len(users)} users", "count": len(users)}