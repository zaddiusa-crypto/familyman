from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.modules.chat.schemas import MessageCreate, MessageResponse, ChatResponse
from app.modules.auth.dependencies import get_db, get_current_user, get_current_active_user
from app.core.models import Chat, Message, User, MessageStatusEnum, MediaTypeEnum
from app.core.rbac import require_permission
from app.core.exceptions import NotFoundError, ValidationError
from app.modules.chat.service import ChatService


router = APIRouter(prefix="/chats", tags=["Chats"])


@router.get("", response_model=List[dict])
async def list_chats(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = current_user.role.value in ["lodge_admin", "super_admin"]
    service = ChatService(db)
    chats = await service.get_chats(current_user.id, current_user.role.value in ["lodge_admin", "super_admin"])

    items = []
    for chat in chats:
        other_user = chat.member if current_user.id == chat.admin_id else chat.member
        unread = chat.unread_admin if current_user.id == chat.admin_id else chat.unread_member
        
        items.append({
            "id": str(chat.id),
            "member_name": chat.member.full_name,
            "member_phone": chat.member.phone,
            "member_country": chat.member.country,
            "last_message": chat.last_message_preview,
            "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
            "unread_count": unread,
            "is_unread": unread > 0,
            "member_avatar": None,
        })

    return items


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from app.core.models import User, Chat

    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can create chats")

    member_id = UUID(data["member_id"])
    member_result = await db.execute(
        select(User).where(User.id == UUID(data["member_id"]), User.lodge_id == current_user.lodge_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    service = ChatService(db)
    chat = await service.get_or_create_chat(member.id, current_user.id)

    return {"chat_id": str(chat.id), "message": "Chat created"}


@router.get("/{chat_id}", response_model=dict)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select
    from app.core.models import Chat

    result = await db.execute(
        select(Chat).options(
            selectinload(Chat.member),
            selectinload(Chat.admin),
        ).where(
            Chat.id == UUID(chat_id),
            Chat.lodge_id == current_user.lodge_id
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    is_admin = current_user.id == chat.admin_id
    other_user = chat.member if is_admin else chat.member

    return {
        "id": str(chat.id),
        "member": {
            "id": str(chat.member.id),
            "full_name": chat.member.full_name,
            "phone": chat.member.phone,
            "country": chat.member.country,
        },
        "subject": chat.subject,
        "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
        "last_message_preview": chat.last_message_preview,
        "unread_count": chat.unread_admin if is_admin else chat.unread_member,
        "is_archived": chat.is_archived,
        "created_at": chat.created_at.isoformat(),
        "updated_at": chat.updated_at.isoformat(),
    }


@router.get("/{chat_id}/messages", response_model=List[dict])
async def get_messages(
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select
    from app.core.models import Message, Chat

    chat_result = await db.execute(
        select(Chat).where(Chat.id == UUID(chat_id), Chat.lodge_id == current_user.lodge_id)
    )
    chat = chat_result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id != chat.member_id and current_user.id != chat.admin_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(Message).options(
            selectinload(Message.sender),
            selectinload(Message.reply_to).selectinload(Message.sender),
        ).where(
            Message.chat_id == UUID(chat_id),
            Message.is_deleted == False,
            ~Message.deleted_for.contains([current_user.id])
        ).order_by(Message.created_at.asc()).limit(limit).offset(offset)
    )
    messages = result.scalars().all()

    items = []
    for msg in messages:
        items.append({
            "id": str(msg.id),
            "chat_id": str(msg.chat_id),
            "sender_id": str(msg.sender_id),
            "sender_name": msg.sender.full_name if msg.sender else "Unknown",
            "sender_is_me": msg.sender_id == current_user.id,
            "content": msg.content,
            "media_url": msg.media_url,
            "media_type": msg.media_type.value if msg.media_type else None,
            "reply_to_id": str(msg.reply_to_id) if msg.reply_to_id else None,
            "reply_preview": None,
            "status": msg.status.value,
            "is_deleted": msg.is_deleted,
            "created_at": msg.created_at.isoformat(),
            "updated_at": msg.updated_at.isoformat(),
        })

    return items


@router.post("/{chat_id}/messages", response_model=dict, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select, update
    from app.core.models import Chat, Message

    chat_result = await db.execute(
        select(Chat).where(Chat.id == UUID(chat_id), Chat.lodge_id == current_user.lodge_id)
    )
    chat = chat_result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id != chat.member_id and current_user.id != chat.admin_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get lodge_id from chat
    lodge_id = chat.lodge_id

    message = Message(
        lodge_id=chat.lodge_id,
        chat_id=UUID(chat_id),
        sender_id=current_user.id,
        content=data.get("content"),
        media_url=data.get("media_url"),
        media_type=data.get("media_type"),
        reply_to_id=UUID(data["reply_to_id"]) if data.get("reply_to_id") else None,
        status="sent",
    )
    db.add(message)
    await db.flush()

    # Update chat last message
    await db.execute(
        update(Chat)
        .where(Chat.id == UUID(chat_id))
        .values(
            last_message_at=datetime.now(timezone.utc),
            last_message_preview=data.get("content", "")[:100] if data.get("content") else "Media",
        )
    )

    # Update unread counts
    if current_user.id == chat.admin_id:
        chat.unread_member += 1
    else:
        chat.unread_admin += 1

    await db.commit()
    await db.refresh(message)

    return {
        "id": str(message.id),
        "chat_id": str(message.chat_id),
        "sender_id": str(message.sender_id),
        "content": message.content,
        "media_url": message.media_url,
        "media_type": message.media_type.value if message.media_type else None,
        "reply_to_id": str(message.reply_to_id) if message.reply_to_id else None,
        "status": message.status.value,
        "created_at": message.created_at.isoformat(),
    }


@router.post("/{chat_id}/read")
async def mark_chat_read(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select, update
    from app.core.models import Chat, Message

    chat_result = await db.execute(
        select(Chat).where(Chat.id == UUID(chat_id), Chat.lodge_id == current_user.lodge_id)
    )
    chat = chat_result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id == chat.admin_id:
        await db.execute(
            update(Chat)
            .where(Chat.id == UUID(chat_id))
            .values(seen_by_admin=datetime.now(timezone.utc), unread_admin=0)
        )
    else:
        await db.execute(
            update(Chat)
            .where(Chat.id == UUID(chat_id))
            .values(seen_by_member=datetime.now(timezone.utc), unread_member=0)
        )

    await db.execute(
        update(Message)
        .where(
            Message.chat_id == UUID(chat_id),
            Message.sender_id != current_user.id,
            Message.status != "read"
        )
        .values(status="read")
    )

    await db.commit()
    return {"message": "Chat marked as read"}


@router.patch("/{chat_id}/messages/{message_id}")
async def edit_message(
    chat_id: str,
    message_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select, update
    from app.core.models import Message

    result = await db.execute(
        select(Message).where(
            Message.id == UUID(message_id),
            Message.chat_id == UUID(chat_id),
            Message.sender_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found or not authorized")

    if "content" in data:
        message.content = data["content"]
        await db.commit()

    return {"message": "Message updated"}


@router.delete("/{chat_id}/messages/{message_id}")
async def delete_message(
    chat_id: str,
    message_id: str,
    for_everyone: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select, update
    from app.core.models import Message

    result = await db.execute(
        select(Message).where(
            Message.id == UUID(message_id),
            Message.chat_id == UUID(chat_id)
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if for_everyone:
        if message.sender_id != current_user.id and current_user.role.value not in ["lodge_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized to delete for everyone")
        message.is_deleted = True
    else:
        deleted_for = list(message.deleted_for)
        if current_user.id not in message.deleted_for:
            message.deleted_for = list(message.deleted_for) + [current_user.id]

    await db.commit()
    return {"message": "Message deleted"}