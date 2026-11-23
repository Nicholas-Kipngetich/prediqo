"""SQLAlchemy models. Import here so Alembic sees the full metadata."""

from app.models import predictions as _predictions  # noqa: F401
from app.models import sports as _sports  # noqa: F401
from app.models.identity import (
    ROLE_PERMISSIONS,
    Permission,
    PermissionCode,
    Profile,
    Role,
    RoleCode,
    User,
    UserStatus,
    role_permissions,
    user_roles,
)

__all__ = [
    "Permission",
    "PermissionCode",
    "Profile",
    "Role",
    "RoleCode",
    "ROLE_PERMISSIONS",
    "User",
    "UserStatus",
    "role_permissions",
    "user_roles",
]
