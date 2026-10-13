import enum
import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoleEnum(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    LODGE_ADMIN = "lodge_admin"
    MEMBER = "member"


class UserStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class ApplicationStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MessageStatusEnum(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class MediaTypeEnum(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    VOICE = "voice"


class NotificationPriorityEnum(str, enum.Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SyncStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class Lodge(Base, TimestampMixin):
    __tablename__ = "lodges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Africa/Nairobi", nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="lodge", lazy="dynamic")
    applications: Mapped[list["Application"]] = relationship(back_populates="lodge", lazy="dynamic")
    chats: Mapped[list["Chat"]] = relationship(back_populates="lodge", lazy="dynamic")
    messages: Mapped[list["Message"]] = relationship(back_populates="lodge", lazy="dynamic")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="lodge", lazy="dynamic")
    announcements: Mapped[list["Announcement"]] = relationship(back_populates="lodge", lazy="dynamic")
    fee_schedules: Mapped[list["FeeSchedule"]] = relationship(back_populates="lodge", lazy="dynamic")
    payments: Mapped[list["Payment"]] = relationship(back_populates="lodge", lazy="dynamic")
    sync_outbox: Mapped[list["SyncOutbox"]] = relationship(back_populates="lodge", lazy="dynamic")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="lodge", lazy="dynamic")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    country_code: Mapped[str | None] = mapped_column(String(5))
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.MEMBER, nullable=False)
    status: Mapped[UserStatusEnum] = mapped_column(
        Enum(UserStatusEnum), default=UserStatusEnum.PENDING, nullable=False
    )
    language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    fcm_tokens: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lodge: Mapped["Lodge"] = relationship(back_populates="users")
    applications: Mapped[list["Application"]] = relationship(back_populates="user", lazy="dynamic")
    sent_messages: Mapped[list["Message"]] = relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender", lazy="dynamic"
    )
    chat_memberships: Mapped[list["Chat"]] = relationship(
        "Chat", foreign_keys="Chat.member_id", back_populates="member", lazy="dynamic"
    )
    assigned_chats: Mapped[list["Chat"]] = relationship(
        "Chat", foreign_keys="Chat.admin_id", back_populates="admin", lazy="dynamic"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", lazy="dynamic")
    sent_announcements: Mapped[list["Announcement"]] = relationship(
        back_populates="author", lazy="dynamic"
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", lazy="dynamic")
    sync_outbox: Mapped[list["SyncOutbox"]] = relationship(back_populates="user", lazy="dynamic")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", foreign_keys="AuditLog.actor_id", back_populates="actor", lazy="dynamic"
    )


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dob: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    id_number: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    birth_town: Mapped[str] = mapped_column(String(100), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    business_type: Mapped[str | None] = mapped_column(String(100))
    business_location: Mapped[str | None] = mapped_column(String(200))
    nearest_lodge: Mapped[str] = mapped_column(String(200), nullable=False)

    status: Mapped[ApplicationStatusEnum] = mapped_column(
        Enum(ApplicationStatusEnum), default=ApplicationStatusEnum.PENDING, nullable=False
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    lodge: Mapped["Lodge"] = relationship(back_populates="applications")
    user: Mapped["User"] = relationship(back_populates="applications")
    reviewer: Mapped[Optional["User"]] = relationship(foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("ix_applications_lodge_status", "lodge_id", "status"),
    )


class Chat(Base, TimestampMixin):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    admin_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    subject: Mapped[str | None] = mapped_column(String(200))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_message_preview: Mapped[str | None] = mapped_column(Text)
    unread_admin: Mapped[int] = mapped_column(Integer, default=0)
    unread_member: Mapped[int] = mapped_column(Integer, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    lodge: Mapped["Lodge"] = relationship(back_populates="chats")
    member: Mapped["User"] = relationship(
        "User", foreign_keys=[member_id], back_populates="chat_memberships"
    )
    admin: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[admin_id], back_populates="assigned_chats"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan", lazy="dynamic"
    )

    __table_args__ = (
        Index("ix_chats_lodge_member", "lodge_id", "member_id"),
        Index("ix_chats_lodge_admin", "lodge_id", "admin_id"),
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str | None] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(String(500))
    media_type: Mapped[MediaTypeEnum | None] = mapped_column(Enum(MediaTypeEnum))
    reply_to_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="SET NULL")
    )
    status: Mapped[MessageStatusEnum] = mapped_column(
        Enum(MessageStatusEnum), default=MessageStatusEnum.SENT, nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_for: Mapped[list[str]] = mapped_column(JSON, default=list)

    lodge: Mapped["Lodge"] = relationship(back_populates="messages")
    chat: Mapped["Chat"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="sent_messages")
    reply_to: Mapped[Optional["Message"]] = relationship(
        remote_side=[id], backref="replies"
    )

    __table_args__ = (
        Index("ix_messages_chat_created", "chat_id", "created_at"),
        Index("ix_messages_lodge_sender", "lodge_id", "sender_id"),
    )


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    priority: Mapped[NotificationPriorityEnum] = mapped_column(
        Enum(NotificationPriorityEnum), default=NotificationPriorityEnum.NORMAL, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_via: Mapped[list[str]] = mapped_column(JSON, default=list)

    lodge: Mapped["Lodge"] = relationship(back_populates="notifications")
    user: Mapped["User"] = relationship(back_populates="notifications")

    __table_args__ = (
        Index(
            "ix_notifications_user_unread",
            "user_id",
            "is_read",
            sqlite_where=text("is_read = 0"),
        ),
        Index("ix_notifications_lodge_created", "lodge_id", "created_at"),
    )


class Announcement(Base, TimestampMixin):
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["member"])
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lodge: Mapped["Lodge"] = relationship(back_populates="announcements")
    author: Mapped["User"] = relationship(back_populates="sent_announcements")


class FeeSchedule(Base, TimestampMixin):
    __tablename__ = "fee_schedules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    lodge: Mapped["Lodge"] = relationship(back_populates="fee_schedules")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fee_schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("fee_schedules.id", ondelete="SET NULL"),
    )
    amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING, nullable=False
    )
    method: Mapped[str | None] = mapped_column(String(30))
    reference: Mapped[str | None] = mapped_column(String(100))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lodge: Mapped["Lodge"] = relationship(back_populates="payments")
    user: Mapped["User"] = relationship(back_populates="payments")
    fee_schedule: Mapped[Optional["FeeSchedule"]] = relationship()

    __table_args__ = (
        Index("ix_payments_lodge_user", "lodge_id", "user_id"),
    )


class SyncOutbox(Base, TimestampMixin):
    __tablename__ = "sync_outbox"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    status: Mapped[SyncStatusEnum] = mapped_column(
        Enum(SyncStatusEnum), default=SyncStatusEnum.PENDING, nullable=False, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lodge: Mapped["Lodge"] = relationship(back_populates="sync_outbox")
    user: Mapped["User"] = relationship(back_populates="sync_outbox")

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_sync_outbox_idempotency"),
        Index("ix_outbox_status_created", "status", "created_at"),
    )


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lodge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lodges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    old_values: Mapped[dict | None] = mapped_column(JSON)
    new_values: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    lodge: Mapped["Lodge"] = relationship(back_populates="audit_logs")
    actor: Mapped["User"] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_lodge_created", "lodge_id", "created_at"),
    )
