"""merge_local_partner_with_main

Revision ID: 4844df17be49
Revises: 1ce0e071d23b, 972a89ccdc8d
Create Date: 2026-06-07 21:18:22.499115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4844df17be49'
down_revision: Union[str, None] = ('1ce0e071d23b', '972a89ccdc8d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
