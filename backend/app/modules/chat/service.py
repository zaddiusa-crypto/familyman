from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Chat, Message


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_chats(self, user_id: UUID, is_admin: bool) -> list:
        if is_admin:
            query = select(Chat).options(
                selectinload(Chat.member),
                selectinload(Chat.messages),
            ).where(Chat.admin_id == user_id)
        else:
            query = select(Chat).options(
                selectinload(Chat.member),
                selectinload(Chat.messages),
            ).where(Chat.member_id == user_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_chat(self, chat_id: UUID, user_id: UUID, is_admin: bool):
        query = select(Chat).where(Chat.id == chat_id)
        if is_admin:
            query = query.where(Chat.admin_id == user_id)
        else:
            query = query.where(Chat.member_id == user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_chat(self, member_id: UUID, admin_id: UUID, subject: str = None) -> Chat:
        chat = Chat(
            lodge_id=member_id,  # Will be set from member's lodge
            member_id=member_id,
            admin_id=member_id,  # Admin will be assigned
            subject=subject,
        )
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)
        return chat

    async def get_or_create_chat(self, member_id: UUID, admin_id: UUID) -> Chat:
        result = await self.db.execute(
            select(Chat).where(
                Chat.member_id == member_id,
                Chat.admin_id == admin_id,
            )
        )
        chat = result.scalar_one_or_none()
        if not chat:
            chat = Chat(
                member_id=member_id,
                admin_id=admin_id,
                subject="New conversation",
            )
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)
        return chat

    async def send_message(self, chat_id: UUID, sender_id: UUID, data: dict) -> Message:
        message = Message(
            lodge_id=data.get("lodge_id"),
            chat_id=chat_id,
            sender_id=sender_id,
            content=data.get("content"),
            media_url=data.get("media_url"),
            media_type=data.get("media_type"),
            reply_to_id=data.get("reply_to_id"),
            status="sent",
        )
        self.db.add(message)
        await self.db.flush()

        # Update chat last message
        from sqlalchemy import update

        from app.core.models import Chat
        await self.db.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(
                last_message_at=datetime.now(UTC),
                last_message_preview=data.get("content", "")[:100] if data.get("content") else "Media",
            )
        )
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(self, chat_id: UUID, user_id: UUID, limit: int = 50, offset: int = 0) -> list:
        from sqlalchemy import select

        from app.core.models import Message

        query = select(Message).options(
            selectinload(Message.sender),
            selectinload(Message.reply_to),
        ).where(
            Message.chat_id == chat_id,
            Message.is_deleted == False,
            Message.deleted_for.cast(String).not_like(f"%{user_id}%")
        ).order_by(Message.created_at.asc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_read(self, chat_id: UUID, user_id: UUID, is_admin: bool):
        from sqlalchemy import update

        from app.core.models import Chat, Message

        chat = await self.get_chat(chat_id, user_id, is_admin)
        if not chat:
            return

        if is_admin:
            await self.db.execute(
                update(Chat)
                .where(Chat.id == chat_id)
                .values(seen_by_admin=datetime.now(UTC), unread_admin=0)
            )
        else:
            await self.db.execute(
                update(Chat)
                .where(Chat.id == chat_id)
                .values(seen_by_member=datetime.now(UTC), unread_member=0)
            )

        # Update message statuses
        await self.db.execute(
            update(Message)
            .where(
                Message.chat_id == chat_id,
                Message.sender_id != user_id,
                Message.status != "read"
            )
            .values(status="read")
        )
        await self.db.commit()

    async def update_message_status(self, message_id: UUID, status: str):
        from sqlalchemy import update

        from app.core.models import Message
        await self.db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(status=status)
        )
        await self.db.commit()

    async def delete_message(self, message_id: UUID, user_id: UUID, for_everyone: bool = False):
        from sqlalchemy import select, update

        from app.core.models import Message

        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()
        if not message:
            return

        if for_everyone:
            await self.db.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(is_deleted=True)
            )
        else:
            deleted_for = list(message.deleted_for)
            if str(user_id) not in deleted_for:
                deleted_for.append(str(user_id))
            await self.db.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(deleted_for=deleted_for)
            )
        await self.db.commit()

    async def edit_message(self, message_id: UUID, user_id: UUID, new_content: str):
        from sqlalchemy import update

        from app.core.models import Message

        await self.db.execute(
            update(Message)
            .where(Message.id == message_id, Message.sender_id == user_id)
            .values(content=new_content)
        )
        await self.db.commit()
