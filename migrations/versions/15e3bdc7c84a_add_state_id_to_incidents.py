"""add state_id to incidents

Revision ID: 15e3bdc7c84a
Revises: b03b9778b864
Create Date: 2026-05-15 02:44:10.718729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15e3bdc7c84a'
down_revision: Union[str, None] = '970b11a4e1be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('incidents', sa.Column('state_id', sa.Integer(), sa.ForeignKey('states.id'), nullable=True))


def downgrade() -> None:
    op.drop_constraint('incidents_state_id_fkey', 'incidents', type_='foreignkey')
    op.drop_column('incidents', 'state_id')
