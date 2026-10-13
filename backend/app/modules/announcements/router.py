from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.modules.announcements.schemas import AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse
from app.modules.auth.dependencies import get_db, get_current_user, get_current_active_user
from app.core.models import Announcement, User, RoleEnum
from app.core.rbac import require_permission
from app.core.exceptions import NotFoundError


router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.get("", response_model=dict)
async def list_announcements(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Announcement).where(
        Announcement.lodge_id == current_user.lodge_id,
        Announcement.is_published == True,
    )

    # Filter by target roles
    if current_user.role.value == "member":
        query = query.where(
            or_(
                Announcement.target_roles.contains(["member"]),
                Announcement.target_roles.contains(["all"]),
            )
        )

    if search:
        query = query.where(
            or_(
                Announcement.title.ilike(f"%{search}%"),
                Announcement.content.ilike(f"%{search}%"),
            )
        )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Announcement.published_at.desc().nullslast()).offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    announcements = result.scalars().all()

    return {
        "items": [
            {
                "id": str(a.id),
                "title": a.title,
                "content": a.content,
                "media_urls": a.media_urls,
                "target_roles": a.target_roles,
                "is_published": a.is_published,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "author_name": a.author.full_name if a.author else "Unknown",
                "created_at": a.created_at.isoformat(),
            }
            for a in announcements
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    announcement = Announcement(
        lodge_id=current_user.lodge_id,
        author_id=current_user.id,
        title=data["title"],
        content=data["content"],
        media_urls=data.get("media_urls", []),
        target_roles=data.get("target_roles", ["member"]),
        is_published=data.get("is_published", True),
        expires_at=data.get("expires_at"),
        published_at=datetime.now(timezone.utc) if data.get("is_published", True) else None,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)

    return {"message": "Announcement created", "announcement_id": str(announcement.id)}


@router.get("/{announcement_id}", response_model=dict)
async def get_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select

    result = await db.execute(
        select(Announcement).options(selectinload(Announcement.author))
        .where(Announcement.id == UUID(announcement_id), Announcement.lodge_id == current_user.lodge_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Check if user can see this announcement
    if current_user.role.value == "member":
        if "member" not in announcement.target_roles and "all" not in announcement.target_roles:
            raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "id": str(announcement.id),
        "title": announcement.title,
        "content": announcement.content,
        "media_urls": announcement.media_urls,
        "target_roles": announcement.target_roles,
        "is_published": announcement.is_published,
        "published_at": announcement.published_at.isoformat() if announcement.published_at else None,
        "expires_at": announcement.expires_at.isoformat() if announcement.expires_at else None,
        "author": {
            "id": str(announcement.author.id),
            "full_name": announcement.author.full_name,
        } if announcement.author else None,
        "created_at": announcement.created_at.isoformat(),
        "updated_at": announcement.updated_at.isoformat(),
    }


@router.patch("/{announcement_id}")
async def update_announcement(
    announcement_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select

    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(Announcement).where(
            Announcement.id == UUID(announcement_id),
            Announcement.lodge_id == current_user.lodge_id
        )
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    for key, value in data.items():
        if hasattr(announcement, key) and value is not None:
            if key == "is_published" and value is True and not announcement.published_at:
                value = datetime.now(timezone.utc)
            setattr(announcement, key, value)

    await db.commit()
    await db.refresh(announcement)

    return {"message": "Announcement updated"}


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    from sqlalchemy import select

    if current_user.role.value not in ["lodge_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(Announcement).where(
            Announcement.id == UUID(announcement_id),
            Announcement.lodge_id == current_user.lodge_id
        )
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    await db.delete(announcement)
    await db.commit()

    return {"message": "Announcement deleted"}