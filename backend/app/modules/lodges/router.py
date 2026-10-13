from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.models import Lodge, User
from app.core.rbac import require_role
from app.modules.auth.dependencies import get_db
from app.modules.lodges.schemas import LodgeCreate, LodgeUpdate

router = APIRouter(prefix="/lodges", tags=["Lodges"])


@router.get("", response_model=dict)
async def list_lodges(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lodge)

    if search:
        query = query.where(
            or_(
                Lodge.name.ilike(f"%{search}%"),
                Lodge.code.ilike(f"%{search}%"),
                Lodge.country.ilike(f"%{search}%"),
            )
        )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Lodge.created_at.desc()).offset((1 - 1) * 20).limit(20)
    result = await db.execute(query)
    lodges = result.scalars().all()

    # Get user counts
    lodge_ids = [l.id for l in lodges]
    user_counts = await db.execute(
        select(User.lodge_id, func.count(User.id))
        .where(User.lodge_id.in_(lodge_ids))
        .group_by(User.lodge_id)
    )
    counts = {str(row[0]): row[1] for row in user_counts}

    return {
        "items": [
            {
                "id": str(l.id),
                "name": l.name,
                "code": l.code,
                "country": l.country,
                "currency": l.currency,
                "user_count": counts.get(str(l.id), 0),
                "created_at": l.created_at.isoformat(),
            }
            for l in lodges
        ],
        "total": total,
        "page": 1,
        "limit": 20,
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_lodge(
    data: LodgeCreate,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    lodge = Lodge(
        name=data.name,
        code=data.code.upper(),
        country=data.country.upper(),
        currency=data.currency.upper(),
        timezone=data.timezone,
        settings=data.settings,
    )
    db.add(lodge)
    try:
        await db.commit()
        await db.refresh(lodge)
    except Exception:
        await db.rollback()
        raise ConflictError("Lodge code already exists")

    return {"message": "Lodge created", "lodge_id": str(lodge.id)}


@router.get("/{lodge_id}", response_model=dict)
async def get_lodge(
    lodge_id: str,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(
        select(Lodge).where(Lodge.id == UUID(lodge_id))
    )
    lodge = result.scalar_one_or_none()
    if not lodge:
        raise HTTPException(status_code=404, detail="Lodge not found")

    # Get user count
    user_count = await db.execute(
        select(func.count(User.id)).where(User.lodge_id == lodge.id)
    )
    user_count = user_count.scalar()

    return {
        "id": str(lodge.id),
        "name": lodge.name,
        "code": lodge.code,
        "country": lodge.country,
        "currency": lodge.currency,
        "timezone": lodge.timezone,
        "settings": lodge.settings,
        "user_count": user_count,
        "created_at": lodge.created_at.isoformat(),
        "updated_at": lodge.updated_at.isoformat(),
    }


@router.patch("/{lodge_id}")
async def update_lodge(
    lodge_id: str,
    data: LodgeUpdate,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(
        select(Lodge).where(Lodge.id == UUID(lodge_id))
    )
    lodge = result.scalar_one_or_none()
    if not lodge:
        raise HTTPException(status_code=404, detail="Lodge not found")

    for key, value in data.dict(exclude_unset=True).items():
        if key == "code":
            value = value.upper()
        elif key == "country":
            value = value.upper()
        elif key == "currency":
            value = value.upper()
        setattr(lodge, key, value)

    await db.commit()
    return {"message": "Lodge updated"}


@router.delete("/{lodge_id}")
async def delete_lodge(
    lodge_id: str,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(
        select(Lodge).where(Lodge.id == UUID(lodge_id))
    )
    lodge = result.scalar_one_or_none()
    if not lodge:
        raise HTTPException(status_code=404, detail="Lodge not found")

    # Check if lodge has users
    user_count = await db.execute(
        select(func.count(User.id)).where(User.lodge_id == lodge.id)
    )
    if user_count.scalar() > 0:
        raise HTTPException(status_code=400, detail="Cannot delete lodge with existing users")

    await db.delete(lodge)
    await db.commit()
    return {"message": "Lodge deleted"}


@router.get("/{lodge_id}/users", response_model=dict)
async def list_lodge_users(
    lodge_id: str,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(select(Lodge).where(Lodge.id == UUID(lodge_id)))
    lodge = result.scalar_one_or_none()
    if not lodge:
        raise HTTPException(status_code=404, detail="Lodge not found")

    query = select(User).where(User.lodge_id == UUID(lodge_id))

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(User.created_at.desc()).offset((1 - 1) * 20).limit(20)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "phone": u.phone,
                "role": u.role.value,
                "status": u.status.value,
                "language": u.language,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        "total": total,
        "page": 1,
        "limit": 20,
    }
