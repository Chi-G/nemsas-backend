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
    # Check if table already exists (in case it was manually created previously in some environments)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if "medical_interventions" not in tables:
        op.create_table('medical_interventions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('patient_id', sa.Integer(), nullable=False),
            sa.Column('is_alert', sa.Boolean(), nullable=True),
            sa.Column('can_speak', sa.Boolean(), nullable=True),
            sa.Column('is_in_pain', sa.Boolean(), nullable=True),
            sa.Column('un_responsive', sa.Boolean(), nullable=True),
            sa.Column('main_complaint', sa.String(), nullable=True),
            sa.Column('primary_survey', sa.String(), nullable=True),
            sa.Column('physical_examination_findings', sa.String(), nullable=True),
            sa.Column('iv_fluid_type', sa.String(), nullable=True),
            sa.Column('size_of_fluid', sa.String(), nullable=True),
            sa.Column('location_of_iv_infusion', sa.String(), nullable=True),
            sa.Column('total_iv_fluid_volume_given', sa.String(), nullable=True),
            sa.Column('oxygen', sa.String(), nullable=True),
            sa.Column('remarks', sa.String(), nullable=True),
            sa.Column('pulse', sa.Integer(), nullable=True),
            sa.Column('blood_pressure', sa.Integer(), nullable=True), # initially Integer
            sa.Column('resp', sa.Integer(), nullable=True),
            sa.Column('glucose', sa.Integer(), nullable=True),
            sa.Column('sp02', sa.Integer(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('medical_intervention_details', sa.String(), nullable=True),
            sa.Column('date_added', sa.DateTime(timezone=True), nullable=True),
            sa.Column('time_taken', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_medical_interventions_id'), 'medical_interventions', ['id'], unique=False)

    op.alter_column('medical_interventions', 'blood_pressure',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('medical_interventions', 'blood_pressure',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)
