"""add monitor_results.baseline for T0/T1 (TD-10)

Revision ID: b6a1baseline001
Revises: ac5a7237aec7
Create Date: 2026-07-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "b6a1baseline001"
down_revision = "ac5a7237aec7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monitor_results",
        sa.Column("baseline", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        op.f("ix_monitor_results_baseline"),
        "monitor_results",
        ["baseline"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_monitor_results_baseline"), table_name="monitor_results")
    op.drop_column("monitor_results", "baseline")
