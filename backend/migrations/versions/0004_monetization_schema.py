"""Create token ledger and subscription schema.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "token_packages",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="KES"),
        sa.Column("google_play_product_id", sa.String(160), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_token_packages_google_play_product_id", "token_packages", ["google_play_product_id"], unique=True)

    op.create_table(
        "token_accounts",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("balance >= 0", name="ck_token_account_balance_nonnegative"),
    )

    op.create_table(
        "token_transactions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", sa.UUID(as_uuid=True), sa.ForeignKey("token_accounts.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(24), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(120), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", sa.String(128), nullable=True),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_token_transaction_idempotency"),
    )
    op.create_index("ix_token_transactions_account_id", "token_transactions", ["account_id"])
    op.create_index("ix_token_transactions_account_created", "token_transactions", ["account_id", "created_at"])

    op.create_table(
        "token_purchases",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("package_id", sa.UUID(as_uuid=True), sa.ForeignKey("token_packages.id"), nullable=False),
        sa.Column("google_play_order_id", sa.String(160), nullable=False),
        sa.Column("google_play_purchase_token", sa.String(512), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="VERIFIED"),
        sa.Column("purchased_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("google_play_order_id", name="uq_token_purchase_order"),
        sa.UniqueConstraint("google_play_purchase_token", name="uq_token_purchase_token"),
    )
    op.create_index("ix_token_purchases_user_id", "token_purchases", ["user_id"])
    op.create_index("ix_token_purchases_package_id", "token_purchases", ["package_id"])

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("interval", sa.String(16), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="KES"),
        sa.Column("google_play_product_id", sa.String(160), nullable=False),
        sa.Column("entitlements_json", sa.String(2000), nullable=False, server_default="[]"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_subscription_plans_code", "subscription_plans", ["code"], unique=True)
    op.create_index("ix_subscription_plans_google_play_product_id", "subscription_plans", ["google_play_product_id"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("purchase_token", sa.String(512), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("purchase_token", name="uq_subscription_purchase_token"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])

    op.create_table(
        "subscription_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("subscription_id", sa.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.String(4000), nullable=False, server_default="{}"),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("idempotency_key", name="uq_subscription_event_idempotency"),
    )
    op.create_index("ix_subscription_events_subscription_id", "subscription_events", ["subscription_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=True),
        sa.Column("target_id", sa.String(128), nullable=True),
        sa.Column("details_json", sa.String(4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])

    op.execute(
        sa.text(
            "INSERT INTO token_packages "
            "(id, name, tokens, price_minor, currency, google_play_product_id, active) VALUES "
            "('d0000000000000000000000000000001', 'Starter', 5, 9900, 'KES', "
            "'com.prediqo.tokens.starter', 1), "
            "('d0000000000000000000000000000002', 'Pro', 20, 29900, 'KES', "
            "'com.prediqo.tokens.pro', 1), "
            "('d0000000000000000000000000000003', 'Elite', 60, 74900, 'KES', "
            "'com.prediqo.tokens.elite', 1)"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO subscription_plans "
            "(id, code, interval, price_minor, currency, google_play_product_id, entitlements_json, active) VALUES "
            "('e0000000000000000000000000000001', 'VIP_MONTHLY', 'MONTHLY', 49900, 'KES', "
            "'com.prediqo.vip.monthly', '[\"predictions:premium:read\",\"analysis:premium:read\"]', 1), "
            "('e0000000000000000000000000000002', 'VIP_ANNUAL', 'ANNUAL', 499000, 'KES', "
            "'com.prediqo.vip.annual', '[\"predictions:premium:read\",\"analysis:premium:read\"]', 1)"
        )
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("subscription_events")
    op.drop_table("subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("token_purchases")
    op.drop_table("token_transactions")
    op.drop_table("token_accounts")
    op.drop_table("token_packages")
