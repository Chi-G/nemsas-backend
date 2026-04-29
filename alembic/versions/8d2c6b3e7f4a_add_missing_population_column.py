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
    # States
    if not column_exists('states', 'population'):
        op.add_column('states', sa.Column('population', sa.Integer(), nullable=False, server_default='0'))
    if not column_exists('states', 'updated_at'):
        op.add_column('states', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
    
    # LGAs
    if not column_exists('lgas', 'population'):
        op.add_column('lgas', sa.Column('population', sa.Integer(), nullable=False, server_default='0'))
    if not column_exists('lgas', 'updated_at'):
        op.add_column('lgas', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
        
    # Drugs
    if not column_exists('drugs', 'dosage_form'):
        op.add_column('drugs', sa.Column('dosage_form', sa.String(length=100), nullable=True))
    if not column_exists('drugs', 'is_nhia_approved'):
        op.add_column('drugs', sa.Column('is_nhia_approved', sa.Boolean(), nullable=False, server_default='true'))
    if not column_exists('drugs', 'is_active'):
        op.add_column('drugs', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    if not column_exists('drugs', 'updated_at'):
        op.add_column('drugs', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))

    # Ambulance Types
    if not column_exists('ambulance_types', 'description'):
        op.add_column('ambulance_types', sa.Column('description', sa.String(length=255), nullable=True))
    if not column_exists('ambulance_types', 'is_active'):
        op.add_column('ambulance_types', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    if not column_exists('ambulance_types', 'updated_at'):
        op.add_column('ambulance_types', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))

    # Accreditation Categories
    if not column_exists('accreditation_categories', 'description'):
        op.add_column('accreditation_categories', sa.Column('description', sa.String(length=255), nullable=True))
    if not column_exists('accreditation_categories', 'is_active'):
        op.add_column('accreditation_categories', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    # Users
    if not column_exists('users', 'provider_id'):
        op.add_column('users', sa.Column('provider_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_users_provider_id'), 'users', ['provider_id'], unique=False)
    if not column_exists('users', 'state_id'):
        op.add_column('users', sa.Column('state_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_users_state_id'), 'users', ['state_id'], unique=False)
    if not column_exists('users', 'lga_id'):
        op.add_column('users', sa.Column('lga_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_users_lga_id'), 'users', ['lga_id'], unique=False)
    if not column_exists('users', 'last_login'):
        op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    if not column_exists('users', 'failed_login_attempts'):
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    if not column_exists('users', 'lockout_until'):
        op.add_column('users', sa.Column('lockout_until', sa.DateTime(), nullable=True))
    if not column_exists('users', 'created_at'):
        op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
    if not column_exists('users', 'updated_at'):
        op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))


def downgrade() -> None:
    # We don't really want to drop these if they might have data, but for completeness:
    pass
