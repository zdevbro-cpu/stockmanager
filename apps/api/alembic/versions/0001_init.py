"""init minimal runnable schema (industry/theme + prices + reco + signals)

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-08

"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "security",
        sa.Column("ticker", sa.String(length=12), primary_key=True),
        sa.Column("name_ko", sa.String(length=200), nullable=False),
        sa.Column("market", sa.String(length=20), nullable=False),
        sa.Column("listed_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "classification_taxonomy",
        sa.Column("taxonomy_id", sa.String(length=50), primary_key=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "classification_node",
        sa.Column("taxonomy_id", sa.String(length=50), sa.ForeignKey("classification_taxonomy.taxonomy_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("code", sa.String(length=80), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("parent_code", sa.String(length=80), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_class_node_tax_parent", "classification_node", ["taxonomy_id", "parent_code"])
    op.create_index("idx_class_node_tax_level", "classification_node", ["taxonomy_id", "level"])

    op.create_table(
        "security_classification",
        sa.Column("ticker", sa.String(length=12), sa.ForeignKey("security.ticker", ondelete="CASCADE"), primary_key=True),
        sa.Column("taxonomy_id", sa.String(length=50), primary_key=True),
        sa.Column("code", sa.String(length=80), primary_key=True),
        sa.Column("effective_from", sa.Date(), primary_key=True, nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_sec_class_ticker", "security_classification", ["ticker"])
    op.create_index("idx_sec_class_tax_code", "security_classification", ["taxonomy_id", "code"])

    op.create_table(
        "price_daily",
        sa.Column("ticker", sa.String(length=12), sa.ForeignKey("security.ticker", ondelete="CASCADE"), primary_key=True),
        sa.Column("trade_date", sa.Date(), primary_key=True),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("turnover_krw", sa.Float(), nullable=True),
    )
    op.create_index("idx_price_daily_date", "price_daily", ["trade_date"])

    op.create_table(
        "recommendation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("strategy_id", sa.String(length=80), nullable=False),
        sa.Column("strategy_version", sa.String(length=20), nullable=False),
        sa.Column("ticker", sa.String(length=12), sa.ForeignKey("security.ticker", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("target_weight", sa.Float(), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("as_of_date", "strategy_id", "strategy_version", "ticker", name="uq_reco_key"),
    )
    op.create_index("idx_reco_lookup", "recommendation", ["as_of_date", "strategy_id", "strategy_version"])

    op.create_table(
        "timing_signal",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(length=12), sa.ForeignKey("security.ticker", ondelete="CASCADE"), nullable=False),
        sa.Column("horizon", sa.String(length=10), nullable=False),
        sa.Column("signal", sa.String(length=10), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("triggers", sa.JSON(), nullable=True),
        sa.Column("risk_flags", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
    )
    op.create_index("idx_signal_lookup", "timing_signal", ["ticker", "horizon", "ts"])


def downgrade() -> None:
    op.drop_index("idx_signal_lookup", table_name="timing_signal")
    op.drop_table("timing_signal")
    op.drop_index("idx_reco_lookup", table_name="recommendation")
    op.drop_table("recommendation")
    op.drop_index("idx_price_daily_date", table_name="price_daily")
    op.drop_table("price_daily")
    op.drop_index("idx_sec_class_tax_code", table_name="security_classification")
    op.drop_index("idx_sec_class_ticker", table_name="security_classification")
    op.drop_table("security_classification")
    op.drop_index("idx_class_node_tax_level", table_name="classification_node")
    op.drop_index("idx_class_node_tax_parent", table_name="classification_node")
    op.drop_table("classification_node")
    op.drop_table("classification_taxonomy")
    op.drop_table("security")
