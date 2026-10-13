from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Application,
    ApplicationStatusEnum,
    Chat,
    Message,
    Notification,
    Payment,
    User,
)
from app.core.rbac import require_permission
from app.modules.admin.schemas import AdminStatsResponse, BroadcastCreate
from app.modules.auth.dependencies import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: User = Depends(require_permission("admin.analytics")),
    db: AsyncSession = Depends(get_db),
):
    # Total users
    total_users = await db.execute(
        select(func.count(User.id)).where(User.lodge_id == current_user.lodge_id)
    )
    total_users = total_users.scalar()

    # Applications
    total_apps = await db.execute(
        select(func.count(Application.id)).where(Application.lodge_id == current_user.lodge_id)
    )
    total_apps = total_apps.scalar()

    pending_apps = await db.execute(
        select(func.count(Application.id)).where(
            Application.lodge_id == current_user.lodge_id,
            Application.status == "pending"
        )
    )
    pending_apps = pending_apps.scalar()

    # Chats
    total_chats = await db.execute(
        select(func.count(Chat.id)).where(Chat.lodge_id == current_user.lodge_id)
    )
    total_chats = total_chats.scalar()

    # Messages
    total_messages = await db.execute(
        select(func.count(Message.id)).where(Message.lodge_id == current_user.lodge_id)
    )
    total_messages = total_messages.scalar()

    # Unread chats
    unread_chats = await db.execute(
        select(func.count(Chat.id)).where(
            Chat.lodge_id == current_user.lodge_id,
            or_(Chat.unread_admin > 0, Chat.unread_member > 0)
        )
    )
    unread_chats = unread_chats.scalar()

    # Payments
    total_payments = await db.execute(
        select(func.count(Payment.id)).where(Payment.lodge_id == current_user.lodge_id)
    )
    total_payments = total_payments.scalar()

    pending_payments = await db.execute(
        select(func.count(Payment.id)).where(
            Payment.lodge_id == current_user.lodge_id,
            Payment.status == "pending"
        )
    )
    pending_payments = pending_payments.scalar()

    # Revenue
    revenue_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            Payment.lodge_id == current_user.lodge_id,
            Payment.status == "completed"
        )
    )
    revenue = revenue_result.scalar() or 0

    # Active users
    now = datetime.now(UTC)
    active_24h = await db.execute(
        select(func.count(User.id)).where(
            User.lodge_id == current_user.lodge_id,
            User.last_login_at >= now - timedelta(hours=24)
        )
    )
    active_24h = active_24h.scalar()

    active_7d = await db.execute(
        select(func.count(User.id)).where(
            User.lodge_id == current_user.lodge_id,
            User.last_login_at >= now - timedelta(days=7)
        )
    )
    active_7d = active_7d.scalar()

    # FCM tokens
    fcm_tokens = await db.execute(
        select(func.count(User.id)).where(
            User.lodge_id == current_user.lodge_id,
            func.json_array_length(User.fcm_tokens) > 0
        )
    )
    fcm_tokens = fcm_tokens.scalar()

    # Sync queue depth
    from app.core.models import SyncOutbox
    sync_queue = await db.execute(
        select(func.count(SyncOutbox.id)).where(
            SyncOutbox.lodge_id == current_user.lodge_id,
            SyncOutbox.status.in_(["pending", "processing"])
        )
    )
    sync_queue = sync_queue.scalar()

    return AdminStatsResponse(
        total_users=total_users,
        total_applications=total_apps,
        pending_applications=pending_apps,
        total_chats=total_chats,
        total_messages=total_messages,
        unread_chats=unread_chats,
        total_payments=total_payments,
        pending_payments=pending_payments,
        revenue=float(revenue),
        active_users_24h=active_24h,
        active_users_7d=active_7d,
        fcm_tokens_count=fcm_tokens,
        sync_queue_depth=sync_queue,
    )


@router.get("/users", response_model=dict)
async def admin_list_users(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    status_filter: str | None = None,
    role_filter: str | None = None,
    current_user: User = Depends(require_permission("admin.users.manage")),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).where(User.lodge_id == current_user.lodge_id)

    if search:
        from sqlalchemy import or_
        query = query.where(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
            )
        )

    if status_filter:
        query = query.where(User.status == status_filter)

    if role_filter:
        query = query.where(User.role == role_filter)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(User.created_at.desc()).offset((1 - 1) * 20).limit(20)
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
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        "total": total,
        "page": 1,
        "limit": 20,
    }


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    data: dict,
    current_user: User = Depends(require_permission("admin.users.manage")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.core.models import User
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
                from app.core.models import RoleEnum
                try:
                    value = RoleEnum(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid role")
            elif key == "status":
                from app.core.models import UserStatusEnum
                try:
                    value = UserStatusEnum(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid status")
            setattr(user, key, value)

    await db.commit()
    return {"message": "User updated"}


@router.get("/applications", response_model=dict)
async def admin_list_applications(
    page: int = 1,
    limit: int = 20,
    status_filter: str | None = None,
    search: str | None = None,
    current_user: User = Depends(require_permission("admin.apps.review")),
    db: AsyncSession = Depends(get_db),
):
    query = select(Application).where(Application.lodge_id == current_user.lodge_id)

    if search:
        from sqlalchemy import or_
        query = query.where(
            or_(
                Application.full_name.ilike(f"%{search}%"),
                Application.id_number.ilike(f"%{search}%"),
            )
        )

    if status_filter:
        query = query.where(Application.status == status_filter)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Application.submitted_at.desc()).offset((1 - 1) * 20).limit(20)
    result = await db.execute(query)
    applications = result.scalars().all()

    # Get user info
    user_ids = [app.user_id for app in applications]
    users_result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users_map = {u.id: u for u in users_result.scalars().all()}

    return {
        "items": [
            {
                "id": str(app.id),
                "full_name": app.full_name,
                "email": users_map.get(app.user_id).email if users_map.get(app.user_id) else None,
                "phone": app.phone,
                "status": app.status.value,
                "submitted_at": app.submitted_at.isoformat(),
                "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
            }
            for app in applications
        ],
        "total": len(applications),
        "page": 1,
        "limit": 20,
    }


@router.patch("/applications/{application_id}/status")
async def admin_update_application_status(
    application_id: str,
    status: str,
    review_notes: str | None = None,
    current_user: User = Depends(require_permission("admin.apps.review")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.core.models import Application

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
    application.reviewed_at = datetime.now(UTC)
    if review_notes:
        application.review_notes = review_notes

    await db.commit()

    return {"message": f"Application status updated to {status}"}


@router.get("/chats", response_model=dict)
async def admin_list_chats(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    current_user: User = Depends(require_permission("admin.chats.monitor")),
    db: AsyncSession = Depends(get_db),
):
    query = select(Chat).where(Chat.lodge_id == current_user.lodge_id)

    if search:
        from sqlalchemy import or_
        query = query.where(
            or_(
                Chat.member.has(User.full_name.ilike(f"%{search}%")),
                Chat.member.has(User.phone.ilike(f"%{search}%")),
            )
        )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Chat.last_message_at.desc().nullslast()).offset((1 - 1) * 20).limit(20)
    result = await db.execute(query)
    chats = result.scalars().all()

    return {
        "items": [
            {
                "id": str(chat.id),
                "member_name": chat.member.full_name,
                "member_phone": chat.member.phone,
                "last_message": chat.last_message_preview,
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
                "unread_admin": chat.unread_admin,
                "is_archived": chat.is_archived,
            }
            for chat in chats
        ],
        "total": total,
        "page": 1,
        "limit": 20,
    }


@router.post("/broadcast", response_model=dict)
async def send_broadcast(
    data: BroadcastCreate,
    current_user: User = Depends(require_permission("admin.broadcast")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.core.models import User

    target_roles = data.target_roles or ["member"]
    query = select(User).where(User.lodge_id == current_user.lodge_id)
    if data.target_roles:
        query = query.where(User.role.in_(data.target_roles))

    result = await db.execute(query)
    users = result.scalars().all()

    notifications = []
    for user in users:
        notification = Notification(
            lodge_id=current_user.lodge_id,
            user_id=user.id,
            type="broadcast",
            title=data.title,
            body=data.body,
            data=data.data,
            priority=data.priority,
        )
        notifications.append(notification)

    db.add_all(notifications)
    await db.commit()

    # Emit via Socket.io
    from app.ws.socketio_app import sio
    await sio.emit("announcement_new", {
        "title": data.title,
        "message": data.body,
        "type": "broadcast",
    }, room=f"lodge:{current_user.lodge_id}")

    return {"message": f"Broadcast sent to {len(users)} users", "count": len(users)}


@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    action: str | None = None,
    current_user: User = Depends(require_permission("admin.analytics")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.core.models import AuditLog

    query = select(AuditLog).where(AuditLog.lodge_id == current_user.lodge_id)

    if action:
        query = query.where(AuditLog.action == action)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * 50).limit(50)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "actor_id": str(log.actor_id),
                "action": log.action,
                "target_type": log.target_type,
                "target_id": str(log.target_id) if log.target_id else None,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/sync-status", response_model=dict)
async def get_sync_status(
    current_user: User = Depends(require_permission("admin.analytics")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.core.models import SyncOutbox, SyncStatusEnum

    pending = await db.execute(
        select(func.count(SyncOutbox.id)).where(
            SyncOutbox.lodge_id == current_user.lodge_id,
            SyncOutbox.status == SyncStatusEnum.PENDING
        )
    )
    pending = pending.scalar()

    processing = await db.execute(
        select(func.count(SyncOutbox.id)).where(
            SyncOutbox.lodge_id == current_user.lodge_id,
            SyncOutbox.status == SyncStatusEnum.PROCESSING
        )
    )
    processing = processing.scalar()

    failed = await db.execute(
        select(func.count(SyncOutbox.id)).where(
            SyncOutbox.lodge_id == current_user.lodge_id,
            SyncOutbox.status == SyncStatusEnum.FAILED
        )
    )
    failed = failed.scalar()

    completed = await db.execute(
        select(func.count(SyncOutbox.id)).where(
            SyncOutbox.lodge_id == current_user.lodge_id,
            SyncOutbox.status == SyncStatusEnum.COMPLETED
        )
    )
    completed = completed.scalar()

    # Recent failures
    result = await db.execute(
        select(SyncOutbox).where(
            SyncOutbox.lodge_id == current_user.lodge_id,
            SyncOutbox.status == SyncStatusEnum.FAILED
        ).order_by(SyncOutbox.created_at.desc()).limit(10)
    )
    recent_failures = result.scalars().all()

    return {
        "pending": pending,
        "processing": processing,
        "failed": failed,
        "completed": completed,
        "recent_failures": [
            {
                "id": str(f.id),
                "table_name": f.table_name,
                "operation": f.operation,
                "last_error": f.last_error,
                "attempts": f.attempts,
                "created_at": f.created_at.isoformat(),
            }
            for f in recent_failures
        ],
    }
