"""add signal config table

Revision ID: 0002_signal_config
Revises: 0001_init
Create Date: 2026-01-20

"""

from alembic import op
import sqlalchemy as sa


revision = "0002_signal_config"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "signal_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine", sa.String(length=50), nullable=False),
        sa.Column("horizons", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("signal_config")
