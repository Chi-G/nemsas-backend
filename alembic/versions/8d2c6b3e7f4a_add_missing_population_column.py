"""add missing population column to states

Revision ID: 8d2c6b3e7f4a
Revises: 201257c7c789
Create Date: 2026-04-29 16:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d2c6b3e7f4a'
down_revision: Union[str, Sequence[str], None] = '201257c7c789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table, column):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = insp.get_columns(table)
    return any(c['name'] == column for c in columns)


def upgrade() -> None:
    if not column_exists('states', 'population'):
        op.add_column('states', sa.Column('population', sa.Integer(), nullable=False, server_default='0'))
    if not column_exists('states', 'updated_at'):
        op.add_column('states', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))


def downgrade() -> None:
    op.drop_column('states', 'updated_at')
    op.drop_column('states', 'population')
