"""Create prediction publication schema.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("feature_version", sa.String(64), nullable=False, server_default="v1"),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metrics_json", sa.String(4000), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="CHALLENGER"),
    )

    op.create_table(
        "prediction_markets",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("market_group", sa.String(64), nullable=False, server_default="other"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_prediction_markets_code", "prediction_markets", ["code"], unique=True)

    op.create_table(
        "predictions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("fixture_id", sa.UUID(as_uuid=True), sa.ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False),
        sa.Column("market_id", sa.UUID(as_uuid=True), sa.ForeignKey("prediction_markets.id"), nullable=False),
        sa.Column("model_version_id", sa.UUID(as_uuid=True), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("probabilities_json", sa.String(4000), nullable=False),
        sa.Column("selected_outcome", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("snapshot_json", sa.String(8000), nullable=False),
        sa.Column("explanation_json", sa.String(4000), nullable=False),
        sa.Column("is_sample_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("fixture_id", "market_id", "model_version_id", name="uq_prediction_fixture_market_model"),
    )
    op.create_index("ix_predictions_fixture_id", "predictions", ["fixture_id"])
    op.create_index("ix_predictions_market_id", "predictions", ["market_id"])
    op.create_index("ix_predictions_model_version_id", "predictions", ["model_version_id"])
    op.create_index("ix_predictions_published_at", "predictions", ["published_at"])

    op.create_table(
        "prediction_settlements",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", sa.UUID(as_uuid=True), sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("result", sa.String(24), nullable=False),
        sa.Column("actual_outcome", sa.String(32), nullable=True),
        sa.Column("source", sa.String(120), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
    )
    op.create_index("ix_prediction_settlements_prediction_id", "prediction_settlements", ["prediction_id"], unique=True)

    op.create_table(
        "model_evaluations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_version_id", sa.UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metrics_json", sa.String(4000), nullable=False),
    )
    op.create_index("ix_model_evaluations_model_version_id", "model_evaluations", ["model_version_id"])

    op.execute(
        sa.text(
            "INSERT INTO model_versions "
            "(id, name, version, feature_version, status, metrics_json) VALUES "
            "('b0000000-0000-0000-0000-000000000001', 'poisson-elo-ensemble', "
            "'v1.0.0', 'v1', 'CHAMPION', '{\"validation\": \"pending\"}')"
        )
    )
    for market_id, code, name, group in [
        ("c0000000-0000-0000-0000-000000000001", "1X2", "Match Result", "result"),
        ("c0000000-0000-0000-0000-000000000002", "OU25", "Over/Under 2.5 Goals", "goals"),
        ("c0000000-0000-0000-0000-000000000003", "BTTS", "Both Teams to Score", "goals"),
        ("c0000000-0000-0000-0000-000000000004", "CS", "Correct Score", "goals"),
    ]:
        op.execute(
            sa.text(
                "INSERT INTO prediction_markets (id, code, name, market_group, active) "
                f"VALUES ('{market_id}', '{code}', '{name}', '{group}', 1)"
            )
        )


def downgrade() -> None:
    op.drop_table("model_evaluations")
    op.drop_table("prediction_settlements")
    op.drop_table("predictions")
    op.drop_table("prediction_markets")
    op.drop_table("model_versions")
