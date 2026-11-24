"""Add phone support and development verification codes.

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(32), nullable=True))
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)
    op.add_column("dev_credentials", sa.Column("verification_code_hash", sa.String(128), nullable=True))
    op.add_column("dev_credentials", sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("dev_credentials", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("dev_credentials", "verified_at")
    op.drop_column("dev_credentials", "verification_expires_at")
    op.drop_column("dev_credentials", "verification_code_hash")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_column("users", "phone")
