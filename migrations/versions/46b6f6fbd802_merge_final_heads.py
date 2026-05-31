"""Merge final heads

Revision ID: 46b6f6fbd802
Revises: a0dd63e0b030, 5e432b82d0be
Create Date: 2026-05-17 20:44:18.708320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46b6f6fbd802'
down_revision: Union[str, None] = ('a0dd63e0b030', '5e432b82d0be')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
