"""Create daily analysis access tracking.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_access",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fixture_id", sa.UUID(as_uuid=True), sa.ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False),
        sa.Column("accessed_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "fixture_id", "accessed_date", name="uq_analysis_access_user_fixture_day"),
    )
    op.create_index("ix_analysis_access_user_id", "analysis_access", ["user_id"])
    op.create_index("ix_analysis_access_fixture_id", "analysis_access", ["fixture_id"])


def downgrade() -> None:
    op.drop_table("analysis_access")
