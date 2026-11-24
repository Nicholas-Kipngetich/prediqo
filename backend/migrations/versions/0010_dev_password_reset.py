"""Add development password reset code columns.

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("dev_credentials", sa.Column("reset_code_hash", sa.String(128), nullable=True))
    op.add_column("dev_credentials", sa.Column("reset_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("dev_credentials", "reset_expires_at")
    op.drop_column("dev_credentials", "reset_code_hash")
