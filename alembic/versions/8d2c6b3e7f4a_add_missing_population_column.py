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
    # Use raw SQL with IF NOT EXISTS for maximum reliability on the live server
    # This bypasses any issues with SQLAlchemy inspection on the existing schema
    
    # States table
    op.execute("ALTER TABLE states ADD COLUMN IF NOT EXISTS population INTEGER DEFAULT 0")
    op.execute("ALTER TABLE states ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()")
    
    # LGAs table
    op.execute("ALTER TABLE lgas ADD COLUMN IF NOT EXISTS population INTEGER DEFAULT 0")
    op.execute("ALTER TABLE lgas ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()")
    
    # Drugs table
    op.execute("ALTER TABLE drugs ADD COLUMN IF NOT EXISTS dosage_form VARCHAR(100)")
    op.execute("ALTER TABLE drugs ADD COLUMN IF NOT EXISTS is_nhia_approved BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE drugs ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE drugs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()")

    # Ambulance Types table
    op.execute("ALTER TABLE ambulance_types ADD COLUMN IF NOT EXISTS description VARCHAR(255)")
    op.execute("ALTER TABLE ambulance_types ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE ambulance_types ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()")

    # Accreditation Categories table
    op.execute("ALTER TABLE accreditation_categories ADD COLUMN IF NOT EXISTS description VARCHAR(255)")
    op.execute("ALTER TABLE accreditation_categories ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE accreditation_categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()")
    
    # Users table additions
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_id INTEGER")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS state_id INTEGER")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lga_id INTEGER")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lockout_until TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now()")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()")


def downgrade() -> None:
    # We don't really want to drop these if they might have data, but for completeness:
    pass
