"""add_unique_enterprise_name

Revision ID: b2e8f4c91d03
Revises: ac5a7237aec7
Create Date: 2026-07-17 15:25:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b2e8f4c91d03"
down_revision: Union[str, None] = "ac5a7237aec7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_enterprises_name"),
        "enterprises",
        ["name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_enterprises_name"), table_name="enterprises")
