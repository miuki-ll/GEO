"""Alembic 迁移 — 合并 B2 与 baseline 两个 heads。"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0d4286009296'
down_revision: Union[str, None] = ('b2e8f4c91d03', 'b6a1baseline001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
