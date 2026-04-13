"""Add auth models

Revision ID: 302d96555d23
Revises: 790c4f720efe
Create Date: 2026-04-08 12:36:55.466866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '302d96555d23'
down_revision: Union[str, Sequence[str], None] = '790c4f720efe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add auth tables."""
    # Create auth_audit_logs table
    op.create_table('auth_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('email_attempted', sa.String(length=255), nullable=True),
        sa.Column('action', sa.Enum('LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'PASSWORD_RESET_REQUEST', 'PASSWORD_RESET_SUCCESS', 'ACCOUNT_ACTIVATION', 'ACCOUNT_LOCKOUT', name='authaction'), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('details', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_tokens table
    op.create_table('user_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('token_type', sa.Enum('RESET', 'TWO_FACTOR', 'ACTIVATION', name='tokentype'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_tokens_token'), 'user_tokens', ['token'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_tokens_token'), table_name='user_tokens')
    op.drop_table('user_tokens')
    op.drop_table('auth_audit_logs')
