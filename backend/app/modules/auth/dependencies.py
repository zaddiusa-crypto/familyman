from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.models import User
from app.core.security import decode_token

security = HTTPBearer(auto_error=False)


async def get_db(request: Request) -> AsyncSession:
    async with AsyncSessionLocal() as session:
        lodge_id = request.headers.get("X-Lodge-ID")
        if lodge_id:
            try:
                UUID(lodge_id)
            except (ValueError, TypeError):
                lodge_id = None
        if lodge_id:
            # Parameterized to prevent SQL injection; is_local=True keeps the
            # setting scoped to the current transaction/session only.
            await session.execute(
                text("SELECT set_config('app.current_lodge_id', :lodge_id, true)"),
                {"lodge_id": lodge_id},
            )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
        if payload.type != "access":
            raise ValueError("Invalid token type")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == UUID(payload.sub)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.status.value != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not approved",
        )
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.type != "access":
            return None
        result = await db.execute(select(User).where(User.id == UUID(payload.sub)))
        return result.scalar_one_or_none()
    except Exception:
        return None
