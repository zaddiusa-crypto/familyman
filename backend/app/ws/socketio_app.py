import socketio
from fastapi import FastAPI
from app.core.config import settings
from app.core.security import decode_token
from app.core.models import User, Chat, Message, MessageStatusEnum
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone
import json


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.ALLOWED_ORIGINS,
    logger=True,
    engineio_logger=True,
)

socketio_app = socketio.ASGIApp(sio, socketio_path="/ws")


@sio.event
async def connect(sid, environ, auth):
    if not auth or not auth.get("token"):
        return False

    try:
        payload = decode_token(auth["token"])
        if payload.type != "access":
            return False
    except Exception:
        return False

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == UUID(payload.sub))
        )
        user = result.scalar_one_or_none()
        if not user:
            return False

        # Store user info in session
        await sio.save_session(sid, {
            "user_id": str(user.id),
            "lodge_id": str(user.lodge_id),
            "role": user.role.value,
            "is_admin": user.role.value in ["lodge_admin", "super_admin"],
        })

        # Join lodge room
        await sio.enter_room(sid, f"lodge:{user.lodge_id}")

        # Join personal room
        await sio.enter_room(sid, f"user:{user.id}")

        # Join admin room if admin
        if user.role.value in ["lodge_admin", "super_admin"]:
            await sio.enter_room(sid, f"admin:{user.lodge_id}")

    return True


@sio.event
async def disconnect(sid):
    pass


@sio.event
async def chat_join(sid, data):
    session = await sio.get_session(sid)
    chat_id = data.get("chat_id")
    if not chat_id:
        return

    await sio.enter_room(sid, f"chat:{chat_id}")

    # Mark chat as read
    session_data = await sio.get_session(sid)
    user_id = UUID(session_data["user_id"])
    is_admin = session_data["is_admin"]

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Chat)
            .where(Chat.id == UUID(chat_id))
            .values(
                seen_by_admin=datetime.now(timezone.utc) if is_admin else Chat.seen_by_admin,
                seen_by_member=datetime.now(timezone.utc) if not is_admin else Chat.seen_by_member,
                unread_admin=0 if is_admin else Chat.unread_admin,
                unread_member=0 if not is_admin else Chat.unread_member,
            )
        )
        await db.commit()


@sio.event
async def chat_leave(sid, data):
    chat_id = data.get("chat_id")
    if chat_id:
        await sio.leave_room(sid, f"chat:{chat_id}")


@sio.event
async def message_send(sid, data):
    session = await sio.get_session(sid)
    user_id = UUID(session["user_id"])
    lodge_id = UUID(session["lodge_id"])
    is_admin = session["is_admin"]

    chat_id = data.get("chat_id")
    content = data.get("content")
    media_url = data.get("media_url")
    media_type = data.get("media_type")
    reply_to_id = data.get("reply_to_id")

    if not chat_id or not content and not media_url:
        return

    async with AsyncSessionLocal() as db:
        # Verify chat exists and user has access
        from app.core.models import Chat
        result = await db.execute(
            select(Chat).where(Chat.id == UUID(chat_id), Chat.lodge_id == lodge_id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            return

        # Create message
        message = Message(
            lodge_id=lodge_id,
            chat_id=UUID(chat_id),
            sender_id=UUID(session["user_id"]),
            content=content,
            media_url=media_url,
            media_type=media_type,
            reply_to_id=UUID(reply_to_id) if reply_to_id else None,
            status="sent",
        )
        db.add(message)
        await db.flush()

        # Update chat
        await db.execute(
            update(Chat)
            .where(Chat.id == UUID(chat_id))
            .values(
                last_message_at=datetime.now(timezone.utc),
                last_message_preview=content[:100] if content else "Media",
            )
        )

        # Update unread counts
        if is_admin:
            chat.unread_member += 1
        else:
            chat.unread_admin += 1

        await db.commit()
        await db.refresh(message)

        # Emit to chat room
        await sio.emit("message_new", {
            "id": str(message.id),
            "chat_id": chat_id,
            "sender_id": str(message.sender_id),
            "sender_name": "You" if message.sender_id == UUID(session["user_id"]) else "Other",
            "content": message.content,
            "media_url": message.media_url,
            "media_type": message.media_type.value if message.media_type else None,
            "reply_to_id": str(message.reply_to_id) if message.reply_to_id else None,
            "status": message.status.value,
            "created_at": message.created_at.isoformat(),
        }, room=f"chat:{chat_id}")

        # Notify other participant via FCM/Telegram (handled by background worker)
        # Emit to admin room for notifications
        if is_admin:
            await sio.emit("notification_admin", {
                "type": "member_message",
                "chat_id": chat_id,
                "member_name": "Member",
                "preview": content[:50] if content else "Media",
            }, room=f"admin:{lodge_id}")
        else:
            await sio.emit("notification_admin", {
                "type": "admin_message",
                "chat_id": chat_id,
                "preview": content[:50] if content else "Media",
            }, room=f"admin:{lodge_id}")


@sio.event
async def message_read(sid, data):
    session = await sio.get_session(sid)
    user_id = UUID(session["user_id"])
    is_admin = session["is_admin"]
    chat_id = data.get("chat_id")

    if not chat_id:
        return

    async with AsyncSessionLocal() as db:
        from app.core.models import Chat, Message
        await db.execute(
            update(Chat)
            .where(Chat.id == UUID(chat_id))
            .values(
                seen_by_admin=datetime.now(timezone.utc) if is_admin else Chat.seen_by_admin,
                seen_by_member=datetime.now(timezone.utc) if not is_admin else Chat.seen_by_member,
                unread_admin=0 if is_admin else Chat.unread_admin,
                unread_member=0 if not is_admin else Chat.unread_member,
            )
        )

        await db.execute(
            update(Message)
            .where(
                Message.chat_id == UUID(chat_id),
                Message.sender_id != UUID(session["user_id"]),
                Message.status != "read"
            )
            .values(status="read")
        )
        await db.commit()


@sio.event
async def typing_start(sid, data):
    session = await sio.get_session(sid)
    chat_id = data.get("chat_id")
    if chat_id:
        await sio.emit("typing_start", {
            "user_id": session["user_id"],
            "chat_id": chat_id,
        }, room=f"chat:{chat_id}", skip_sid=sid)


@sio.event
async def typing_stop(sid, data):
    chat_id = data.get("chat_id")
    if chat_id:
        session = await sio.get_session(sid)
        await sio.emit("typing_stop", {
            "user_id": session["user_id"],
            "chat_id": chat_id,
        }, room=f"chat:{chat_id}", skip_sid=sid)


# Admin broadcast event
@sio.event
async def admin_broadcast(sid, data):
    session = await sio.get_session(sid)
    if not session.get("is_admin"):
        return

    message = data.get("message")
    target = data.get("target", "all")  # all, lodge_admin, member

    await sio.emit("announcement_new", {
        "title": data.get("title"),
        "message": message,
        "type": "broadcast",
    }, room=f"lodge:{session['lodge_id']}")