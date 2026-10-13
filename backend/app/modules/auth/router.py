from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from app.core.security import create_token_pair, decode_token
from app.modules.auth.dependencies import get_current_active_user, get_db
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    RefreshTokenRequest,
    RegisterApplicationRequest,
    ResetPasswordRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, lodge_id = await service.register(data.model_dump())
    token_pair = create_token_pair(str(user.id), user.role.value, str(user.lodge_id))
    return token_pair


@router.post("/login", response_model=TokenPair)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, lodge_id = await service.login(data.email, data.password)

    from app.core.security import create_token_pair
    token_pair = create_token_pair(str(user.id), user.role.value, str(user.lodge_id))

    if data.remember_me:
        pass  # Refresh token already has 30 days expiry

    return token_pair


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        from app.core.security import create_token_pair, decode_token
        payload = decode_token(data.refresh_token)
        if payload.type != "refresh":
            raise ValueError("Invalid token type")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    from uuid import UUID

    from app.core.models import User

    result = await db.execute(select(User).where(User.id == UUID(payload.sub)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    token_pair = create_token_pair(str(user.id), user.role.value, str(user.lodge_id))
    return token_pair


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.auth.service import AuthService
    service = AuthService(db)
    user = await service.update_profile(current_user.id, data)
    return user


@router.post("/fcm-token")
async def update_fcm_token(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.update_fcm_token(current_user.id, token)
    return {"message": "FCM token updated"}


@router.post("/telegram-link")
async def link_telegram(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.update_telegram_chat_id(current_user.id, chat_id)
    return {"message": "Telegram linked successfully"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    from app.core.models import User

    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()

    if user:
        # TODO: Send password reset email
        pass

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    from uuid import UUID

    from sqlalchemy import select

    from app.core.models import User
    from app.core.security import get_password_hash

    try:
        payload = decode_token(data.token)
        if payload.type != "refresh":
            raise ValueError("Invalid token type")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == UUID(payload.sub)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = get_password_hash(data.new_password)
    await db.commit()

    return {"message": "Password reset successfully"}


@router.post("/register-application", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_application(
    data: RegisterApplicationRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.core.models import Application, ApplicationStatusEnum, Lodge

    # Find or create user
    # This is for guest applications (before login)
    lodge_result = await db.execute(select(Lodge).where(Lodge.code == data.nearest_lodge.split()[-1]))
    lodge = lodge_result.scalar_one_or_none()
    if not lodge:
        raise HTTPException(status_code=404, detail="Lodge not found")

    application = Application(
        lodge_id=lodge.id,
        user_id=None,  # Guest application; linked when the user registers
        full_name=data.full_name,
        dob=data.dob,
        id_number=data.id_number,
        gender=data.gender,
        birth_town=data.birth_town,
        nickname=data.nickname,
        country=data.country,
        phone=data.phone,
        business_type=data.business_type,
        business_location=data.business_location,
        nearest_lodge=data.nearest_lodge,
        status=ApplicationStatusEnum.PENDING,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    return {"message": "Application submitted successfully", "application_id": str(application.id)}
