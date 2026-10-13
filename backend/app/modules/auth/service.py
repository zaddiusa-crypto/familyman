from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.models import User, Lodge, RoleEnum, UserStatusEnum, Application, ApplicationStatusEnum
from app.core.security import get_password_hash, verify_password, create_token_pair, decode_token
from app.core.exceptions import AuthenticationError, ValidationError, ConflictError, NotFoundError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: dict) -> tuple[User, str]:
        lodge = await self.db.execute(
            select(Lodge).where(Lodge.code == data["lodge_code"])
        )
        lodge = lodge.scalar_one_or_none()
        if not lodge:
            raise NotFoundError("Lodge not found")

        user = User(
            lodge_id=lodge.id,
            email=data["email"].lower(),
            password_hash=get_password_hash(data["password"]),
            full_name=data["full_name"],
            phone=data.get("phone"),
            country_code=data.get("country_code"),
            language=data.get("language", "en"),
            role=RoleEnum.MEMBER,
            status=UserStatusEnum.PENDING,
        )
        self.db.add(user)
        await self.db.flush()

        application = Application(
            lodge_id=lodge.id,
            user_id=user.id,
            full_name=data["full_name"],
            dob=data["dob"],
            id_number=data["id_number"],
            gender=data["gender"],
            birth_town=data["birth_town"],
            nickname=data.get("nickname"),
            country=data["country"],
            phone=data["phone"],
            business_type=data.get("business_type"),
            business_location=data.get("business_location"),
            nearest_lodge=data["nearest_lodge"],
            status=ApplicationStatusEnum.PENDING,
        )
        self.db.add(application)

        try:
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("Email already registered")

        return user, lodge.id

    async def login(self, email: str, password: str) -> tuple[User, str]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if user.status == UserStatusEnum.REJECTED:
            raise AuthenticationError("Account rejected")
        if user.status == UserStatusEnum.SUSPENDED:
            raise AuthenticationError("Account suspended")

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        return user, str(user.lodge_id)

    async def refresh_token(self, refresh_token: str) -> dict:
        from app.core.security import decode_token, create_token_pair
        try:
            payload = decode_token(refresh_token)
            if payload.type != "refresh":
                raise AuthenticationError("Invalid token type")
        except Exception:
            raise AuthenticationError("Invalid refresh token")

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(payload.sub))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise AuthenticationError("User not found")

        return create_token_pair(str(user.id), user.role.value, str(user.lodge_id))

    async def update_fcm_token(self, user_id: uuid.UUID, token: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")

        if token not in user.fcm_tokens:
            user.fcm_tokens = list(set(user.fcm_tokens + [token]))
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def update_telegram_chat_id(self, user_id: uuid.UUID, chat_id: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")

        user.telegram_chat_id = chat_id
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        return user

    async def update_profile(self, user_id: uuid.UUID, data: dict) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")

        for key, value in data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user