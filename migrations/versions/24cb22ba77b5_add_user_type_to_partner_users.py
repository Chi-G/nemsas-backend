"""add user_type to partner_users

Revision ID: 24cb22ba77b5
Revises: 972a89ccdc8d
Create Date: 2026-06-08 07:07:29.023973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24cb22ba77b5'
down_revision: Union[str, None] = '972a89ccdc8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
