from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Notification, NotificationPriorityEnum, User
from app.core.config import settings


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: UUID,
        lodge_id: UUID,
        type: str,
        title: str,
        body: str,
        data: dict = None,
        priority: NotificationPriorityEnum = NotificationPriorityEnum.NORMAL,
    ) -> Notification:
        notification = Notification(
            lodge_id=lodge_id,
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data or {},
            priority=priority,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def create_broadcast(
        self,
        lodge_id: UUID,
        title: str,
        body: str,
        data: dict = None,
        priority: NotificationPriorityEnum = NotificationPriorityEnum.NORMAL,
        target_roles: list = None,
    ) -> int:
        from app.core.models import User, RoleEnum

        query = select(User).where(User.lodge_id == UUID(self.lodge_id))
        if target_roles:
            query = query.where(User.role.in_(target_roles))

        result = await self.db.execute(query)
        users = result.scalars().all()

        notifications = []
        for user in users:
            notification = Notification(
                lodge_id=UUID(self.lodge_id),
                user_id=user.id,
                type="broadcast",
                title=title,
                body=body,
                data=data or {},
                priority=priority,
            )
            notifications.append(notification)

        self.db.add_all(notifications)
        await self.db.commit()
        return len(notifications)

    async def get_user_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
        unread_only: bool = False,
    ):
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)

        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = result.scalar()

        query = query.order_by(Notification.created_at.desc()).offset((1 - 1) * 20).limit(20)
        result = await self.db.execute(query)
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
            "total": 0,
            "page": 1,
            "limit": 20,
        }

    async def mark_read(self, notification_id: UUID, user_id: UUID):
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return False

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def mark_all_read(self, user_id: UUID):
        await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

    async def get_unread_count(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        return result.scalar() or 0