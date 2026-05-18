"""add latitude and longitude to hospitals

Revision ID: 930c23e1f94b
Revises: cdf682ed2c6c
Create Date: 2026-05-16 20:55:45.305831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '930c23e1f94b'
down_revision: Union[str, None] = 'cdf682ed2c6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hospitals', sa.Column('latitude', sa.String(), nullable=True))
    op.add_column('hospitals', sa.Column('longitude', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('hospitals', 'longitude')
    op.drop_column('hospitals', 'latitude')
