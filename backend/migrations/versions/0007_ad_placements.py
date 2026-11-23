"""Create ad placement configuration (all disabled by default).

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLACEMENTS = [
    ("app_open", "App open", "APP_OPEN", "ca-app-pub-3940256099942544/9235187345", 1),
    ("banner_home", "Home banner", "BANNER", "ca-app-pub-3940256099942544/6300978111", 1),
    ("native_feed", "Native feed", "NATIVE", "ca-app-pub-3940256099942544/3130260592", 0),
    ("interstitial_navigation", "Navigation interstitial", "INTERSTITIAL", "ca-app-pub-3940256099942544/1033173712", 0),
    ("rewarded_unlock", "Rewarded unlock", "REWARDED", "ca-app-pub-3940256099942544/6498350057", 0),
]


def upgrade() -> None:
    op.create_table(
        "ad_placements",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("ad_type", sa.String(32), nullable=False),
        sa.Column("unit_id", sa.String(256), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("frequency_cap_per_hour", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("vip_excluded", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ad_placements_key", "ad_placements", ["key"], unique=True)

    op.create_table(
        "system_config",
        sa.Column("key", sa.String(120), primary_key=True),
        sa.Column("value_json", sa.String(4000), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    for index, (key, name, ad_type, unit_id, enabled) in enumerate(PLACEMENTS, start=1):
        op.execute(
            sa.text(
                "INSERT INTO ad_placements "
                "(id, key, name, ad_type, unit_id, enabled, frequency_cap_per_hour, vip_excluded) "
                f"VALUES ('f000000000000000000000000000000{index:02d}', '{key}', '{name}', "
                f"'{ad_type}', '{unit_id}', {enabled}, 2, 1)"
            )
        )

    op.execute(
        sa.text(
            "INSERT INTO system_config (key, value_json) VALUES "
            "('ads_enabled', 'true'), "
            "('ads_policy_reviewed', 'true'), "
            "('admob_app_id_android', '\"ca-app-pub-3940256099942544~3347511713\"')"
        )
    )


def downgrade() -> None:
    op.drop_table("system_config")
    op.drop_table("ad_placements")
