from enum import Enum
from functools import wraps
from typing import Set
from fastapi import Depends, HTTPException, status
from app.core.models import RoleEnum
from app.modules.auth.dependencies import get_current_user
from app.core.models import User


class Permission(str, Enum):
    ADMIN_DASHBOARD = "admin.dashboard"
    ADMIN_USERS_MANAGE = "admin.users.manage"
    ADMIN_APPS_REVIEW = "admin.applications.review"
    ADMIN_BROADCAST = "admin.broadcast"
    ADMIN_ANALYTICS = "admin.analytics"
    ADMIN_SETTINGS = "admin.settings"
    ADMIN_CHATS_MONITOR = "admin.chats.monitor"

    MEMBER_PROFILE = "member.profile"
    MEMBER_APPLICATIONS = "member.applications"
    MEMBER_CHATS = "member.chats"
    MEMBER_PAYMENTS = "member.payments"
    MEMBER_DOCUMENTS = "member.documents"


ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "super_admin": {
        Permission.ADMIN_DASHBOARD, Permission.ADMIN_USERS_MANAGE,
        Permission.ADMIN_APPS_REVIEW, Permission.ADMIN_BROADCAST,
        Permission.ADMIN_ANALYTICS, Permission.ADMIN_SETTINGS,
        Permission.ADMIN_CHATS_MONITOR,
        Permission.MEMBER_PROFILE, Permission.MEMBER_APPLICATIONS,
        Permission.MEMBER_CHATS, Permission.MEMBER_PAYMENTS,
        Permission.MEMBER_DOCUMENTS,
    },
    "lodge_admin": {
        Permission.ADMIN_DASHBOARD, Permission.ADMIN_USERS_MANAGE,
        Permission.ADMIN_APPS_REVIEW, Permission.ADMIN_BROADCAST,
        Permission.ADMIN_CHATS_MONITOR,
        Permission.MEMBER_PROFILE, Permission.MEMBER_APPLICATIONS,
        Permission.MEMBER_CHATS, Permission.MEMBER_PAYMENTS,
        Permission.MEMBER_DOCUMENTS,
    },
    "member": {
        Permission.MEMBER_PROFILE, Permission.MEMBER_APPLICATIONS,
        Permission.MEMBER_CHATS, Permission.MEMBER_PAYMENTS,
        Permission.MEMBER_DOCUMENTS,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """Dependency that checks if current user has the required permission."""
    async def _check(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user.role.value, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission.value}' required"
            )
        return current_user
    return _check


def require_role(*roles: str):
    """Dependency that checks if current user has one of the required roles."""
    async def _check(current_user: User = Depends(get_current_user)):
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role {' or '.join(roles)} required"
            )
        return current_user
    return _check