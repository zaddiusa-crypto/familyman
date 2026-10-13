import asyncio
import logging

import httpx
from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.models import User

logger = logging.getLogger(__name__)


class FCMDispatcher:
    def __init__(self):
        self.vapid_public = settings.FCM_VAPID_PUBLIC_KEY
        self.vapid_private = settings.FCM_VAPID_PRIVATE_KEY
        self.fcm_url = f"https://fcm.googleapis.com/v1/projects/{settings.FCM_PROJECT_ID}/messages:send"

    async def send_to_token(self, token: str, title: str, body: str, data: dict = None) -> bool:
        headers = {
            "Authorization": f"Bearer {await self._get_access_token()}",
            "Content-Type": "application/json",
        }

        payload = {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body,
                },
                "data": data or {},
                "android": {
                    "priority": "high",
                    "notification": {
                        "channel_id": "mff_chat",
                        "priority": "high",
                        "default_sound": True,
                        "default_vibrate_timings": True,
                    },
                },
                "apns": {
                    "payload": {
                        "aps": {
                            "sound": "default",
                            "badge": 1,
                        }
                    }
                },
                "webpush": {
                    "notification": {
                        "icon": "/icon-192.png",
                        "badge": "/icon-192.png",
                        "requireInteraction": True,
                    }
                },
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.fcm_url, json=payload, headers=headers, timeout=10)
                if resp.status_code == 200:
                    return True
                else:
                    logger.error(f"FCM send failed: {resp.status_code} - {resp.text}")
                    return False
            except Exception as e:
                logger.error(f"FCM send error: {e}")
                return False

    async def _get_access_token(self) -> str:
        # TODO: Implement OAuth2 token generation from service account
        # For now, return a placeholder
        return "FCM_ACCESS_TOKEN"


async def process_notification_queue():
    """Background worker to process pending notifications and send via FCM."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Get pending high-priority notifications
                from app.core.models import Notification, NotificationPriorityEnum
                result = await db.execute(
                    select(Notification).where(
                        Notification.is_read == False,
                        Notification.sent_via.notilike("%fcm%"),
                        Notification.priority == NotificationPriorityEnum.HIGH
                    ).limit(50)
                )
                notifications = result.scalars().all()

                dispatcher = FCMDispatcher()

                for notification in notifications:
                    # Get user's FCM tokens
                    result = await db.execute(
                        select(User).where(User.id == notification.user_id)
                    )
                    user = result.scalar_one_or_none()
                    if not user or not user.fcm_tokens:
                        continue

                    success_count = 0
                    for token in user.fcm_tokens:
                        success = await dispatcher.send_to_token(
                            token=token,
                            title=notification.title,
                            body=notification.body,
                            data={
                                "notification_id": str(notification.id),
                                "type": notification.type,
                                **notification.data,
                            },
                        )
                        if success:
                            success_count += 1

                    if success_count > 0:
                        # Mark as sent via FCM
                        sent_via = list(notification.sent_via)
                        if "fcm" not in sent_via:
                            sent_via.append("fcm")
                        await db.execute(
                            update(Notification)
                            .where(Notification.id == notification.id)
                            .values(sent_via=sent_via)
                        )
                        await db.commit()

        except Exception as e:
            logging.error(f"FCM dispatcher error: {e}")

        await asyncio.sleep(10)  # Process every 10 seconds


async def main():
    await process_notification_queue()


if __name__ == "__main__":
    asyncio.run(main())
