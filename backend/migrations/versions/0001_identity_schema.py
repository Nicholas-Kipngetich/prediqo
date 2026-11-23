"""Create identity and access-control schema.

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROLES = [
    {"id": 1, "code": "USER", "description": "Registered user"},
    {"id": 2, "code": "VIP_USER", "description": "Active VIP subscriber"},
    {"id": 3, "code": "ADMIN", "description": "Administrator"},
    {"id": 4, "code": "SUPER_ADMIN", "description": "Super administrator"},
]

PERMISSIONS = [
    {"id": 1, "code": "predictions:free:read", "description": "Read free predictions"},
    {"id": 2, "code": "predictions:premium:read", "description": "Read premium predictions"},
    {"id": 3, "code": "analysis:premium:read", "description": "Read premium analysis"},
    {"id": 4, "code": "history:extended:read", "description": "Read extended history"},
    {"id": 5, "code": "admin:users:write", "description": "Manage users"},
    {"id": 6, "code": "admin:system:read", "description": "Read system health"},
]

ROLE_PERMISSIONS = [
    (1, 1),
    (2, 1), (2, 2), (2, 3), (2, 4),
    (3, 1), (3, 2), (3, 5), (3, 6),
    (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
]


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
    )
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("firebase_uid", sa.String(128), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "profiles",
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Africa/Nairobi"),
        sa.Column("locale", sa.String(16), nullable=False, server_default="en"),
        sa.Column("theme", sa.String(16), nullable=False, server_default="dark"),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("avatar_url", sa.String(512), nullable=True),
    )

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    op.bulk_insert(sa.table("permissions", sa.column("id", sa.Integer), sa.column("code", sa.String), sa.column("description", sa.String)), PERMISSIONS)
    op.bulk_insert(sa.table("roles", sa.column("id", sa.Integer), sa.column("code", sa.String), sa.column("description", sa.String)), ROLES)
    op.bulk_insert(
        sa.table(
            "role_permissions",
            sa.column("role_id", sa.Integer),
            sa.column("permission_id", sa.Integer),
        ),
        [{"role_id": r, "permission_id": p} for r, p in ROLE_PERMISSIONS],
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("profiles")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
