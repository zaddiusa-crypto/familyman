import asyncio
import logging
from uuid import UUID

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.models import User

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split()
    if len(args) > 1:
        user_id = args[1]
        await link_telegram_chat(user_id, message.chat.id)
        await message.answer("✅ Linked! You'll receive admin alerts here.")
    else:
        await message.answer("Use the link from your admin dashboard to link your account.")


async def link_telegram_chat(user_id: str, chat_id: int):
    async with AsyncSessionLocal() as db:
        from uuid import UUID
        result = await db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user:
            user.telegram_chat_id = str(chat_id)
            await db.commit()
            logger.info(f"Linked Telegram chat {chat_id} to user {user_id}")


async def send_admin_alert(user_id: UUID, event_type: str, title: str, body: str, data: dict = None):
    """Send alert to admin's Telegram chat."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.telegram_chat_id:
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="View in App", url=f"https://app.familyman.app{data.get('deep_link', '')}"),
            InlineKeyboardButton(text="Dismiss", callback_data=f"dismiss_{data.get('event_id', '')}"),
        ]]) if data else None

    try:
        await bot.send_message(
            chat_id=user.telegram_chat_id,
            text=f"🔔 <b>{title}</b>\n{body}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        logger.info(f"Telegram alert sent to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")


# Event routing
ADMIN_EVENT_ROUTES = {
    "new_application": {"telegram": True, "fcm": True, "dashboard": True},
    "member_message": {"telegram": True, "fcm": True, "dashboard": True},
    "payment_failed": {"telegram": True, "fcm": True, "dashboard": True},
    "payment_received": {"telegram": False, "fcm": True, "dashboard": True},
    "announcement": {"telegram": False, "fcm": True, "dashboard": True},
    "sync_stuck": {"telegram": True, "fcm": False, "dashboard": True},
    "weekly_report": {"telegram": True, "fcm": False, "dashboard": True},
}


async def dispatch_admin_event(event_type: str, user_id: UUID, title: str, body: str, data: dict = None):
    routes = ADMIN_EVENT_ROUTES.get(event_type, {"telegram": True, "fcm": True, "dashboard": True})

    if routes.get("telegram"):
        await send_admin_alert(user_id, event_type, title, body, data)


async def process_telegram_queue():
    """Background worker to process Telegram alerts."""
    # This would be triggered by events from the main application
    # For now, we'll just keep the bot running
    await dp.start_polling(bot)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
