import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.models import Application, Message, Notification, Payment, User

logger = logging.getLogger(__name__)


async def send_daily_digest():
    """Send daily digest to all admins via Telegram."""
    async with AsyncSessionLocal() as db:
        # Get all admins with telegram_chat_id
        result = await db.execute(
            select(User).where(
                User.role.in_(["lodge_admin", "super_admin"]),
                User.telegram_chat_id.isnot(None)
            )
        )
        admins = result.scalars().all()

        now = datetime.now(UTC)
        yesterday = datetime.now(UTC) - timedelta(days=1)

        for admin in admins:
            if not admin.telegram_chat_id:
                continue

            # Get stats for the last 24 hours
            new_apps = await db.execute(
                select(func.count(Application.id)).where(
                    Application.lodge_id == admin.lodge_id,
                    Application.submitted_at >= yesterday
                ))
            new_apps = new_apps.scalar()

            new_payments = await db.execute(
                select(func.count(Payment.id)).where(
                    Payment.lodge_id == admin.lodge_id,
                    Payment.created_at >= yesterday,
                    Payment.status == "completed"
                ))
            new_payments = new_payments.scalar()

            revenue = await db.execute(
                select(func.sum(Payment.amount)).where(
                    Payment.lodge_id == admin.lodge_id,
                    Payment.created_at >= yesterday,
                    Payment.status == "completed"
                ))
            revenue = revenue.scalar() or 0

            new_messages = await db.execute(
                select(func.count(Message.id)).where(
                    Message.lodge_id == admin.lodge_id,
                    Message.created_at >= yesterday
                ))
            new_messages = new_messages.scalar()

            unread_notifs = await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.user_id == admin.id,
                    Notification.is_read == False
                ))
            unread_notifs = unread_notifs.scalar()

            # Build digest message
            message = f"""
📊 <b>Daily Digest - {datetime.now().strftime('%Y-%m-%d')}</b>

📝 New Applications: {new_apps}
💳 Payments Received: {new_payments} (${revenue:,.2f})
💬 New Messages: {new_messages}
🔔 Unread Notifications: {unread_notifs}

<i>Generated at {datetime.now().strftime('%H:%M')} UTC</i>
"""

            try:
                from aiogram import Bot
                bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=admin.telegram_chat_id,
                    text=message,
                    parse_mode="HTML",
                )
            except Exception as e:
                logging.error(f"Failed to send digest to admin {admin.id}: {e}")

    logger.info("Daily digest sent")


async def send_weekly_report():
    """Send weekly report to admins."""
    # Similar to daily but with weekly stats
    pass


async def run_digest_scheduler():
    """Run digest scheduler."""
    while True:
        try:
            now = datetime.now(UTC)
            # Send at 8 AM UTC daily
            if now.hour == 8 and now.minute < 5:
                await send_daily_digest()
                # Wait until next day
                await asyncio.sleep(23 * 60 * 60)
            else:
                await asyncio.sleep(60)
        except Exception as e:
            logging.error(f"Digest scheduler error: {e}")
            await asyncio.sleep(60)


async def main():
    await run_digest_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
