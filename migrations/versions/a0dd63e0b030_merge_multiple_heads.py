"""merge multiple heads

Revision ID: a0dd63e0b030
Revises: 15e3bdc7c84a, b03b9778b864
Create Date: 2026-05-16 11:21:07.652479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0dd63e0b030'
down_revision: Union[str, None] = ('15e3bdc7c84a', 'b03b9778b864')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
