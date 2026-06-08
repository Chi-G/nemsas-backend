"""Merge multiple heads

Revision ID: 7b8210e3ca34
Revises: 2260212b8a0d, 24cb22ba77b5
Create Date: 2026-06-08 09:21:48.879140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b8210e3ca34'
down_revision: Union[str, None] = ('2260212b8a0d', '24cb22ba77b5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
