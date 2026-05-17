"""change_blood_pressure_to_string

Revision ID: ed503b3b9071
Revises: b80c19d3e1ec
Create Date: 2026-05-17 03:30:14.672326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed503b3b9071'
down_revision: Union[str, None] = 'b80c19d3e1ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('medical_interventions', 'blood_pressure',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('medical_interventions', 'blood_pressure',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)
