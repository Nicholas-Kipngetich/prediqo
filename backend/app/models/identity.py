"""Identity and access-control tables."""

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserStatus:
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class RoleCode:
    USER = "USER"
    VIP_USER = "VIP_USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class PermissionCode:
    PREDICTIONS_FREE_READ = "predictions:free:read"
    PREDICTIONS_PREMIUM_READ = "predictions:premium:read"
    ANALYSIS_PREMIUM_READ = "analysis:premium:read"
    HISTORY_EXTENDED_READ = "history:extended:read"
    ADMIN_USERS_WRITE = "admin:users:write"
    ADMIN_SYSTEM_READ = "admin:system:read"


ROLE_PERMISSIONS = {
    RoleCode.USER: [PermissionCode.PREDICTIONS_FREE_READ],
    RoleCode.VIP_USER: [
        PermissionCode.PREDICTIONS_FREE_READ,
        PermissionCode.PREDICTIONS_PREMIUM_READ,
        PermissionCode.ANALYSIS_PREMIUM_READ,
        PermissionCode.HISTORY_EXTENDED_READ,
    ],
    RoleCode.ADMIN: [
        PermissionCode.PREDICTIONS_FREE_READ,
        PermissionCode.PREDICTIONS_PREMIUM_READ,
        PermissionCode.ADMIN_USERS_WRITE,
        PermissionCode.ADMIN_SYSTEM_READ,
    ],
    RoleCode.SUPER_ADMIN: [
        PermissionCode.PREDICTIONS_FREE_READ,
        PermissionCode.PREDICTIONS_PREMIUM_READ,
        PermissionCode.ANALYSIS_PREMIUM_READ,
        PermissionCode.HISTORY_EXTENDED_READ,
        PermissionCode.ADMIN_USERS_WRITE,
        PermissionCode.ADMIN_SYSTEM_READ,
    ],
}


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_status", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=UserStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped["Profile"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    roles: Mapped[list["Role"]] = relationship(secondary=user_roles, lazy="selectin")

    @property
    def role_codes(self) -> set[str]:
        return {role.code for role in self.roles}

    @property
    def is_vip(self) -> bool:
        return RoleCode.VIP_USER in self.role_codes or RoleCode.SUPER_ADMIN in self.role_codes


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    timezone: Mapped[str] = mapped_column(String(64), default="Africa/Nairobi")
    locale: Mapped[str] = mapped_column(String(16), default="en")
    theme: Mapped[str] = mapped_column(String(16), default="dark")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, lazy="selectin"
    )


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("code", name="uq_permissions_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
