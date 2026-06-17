"""approve_existing_ambulances_and_hospitals

Revision ID: c8eb52b9c7df
Revises: 8bd595b1e036
Create Date: 2026-06-17 12:22:35.256429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8eb52b9c7df'
down_revision: Union[str, None] = '8bd595b1e036'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE hospitals SET status = 'approved' WHERE status IS NULL OR status != 'approved'"))
    conn.execute(sa.text("UPDATE ambulances SET status = 'approved' WHERE status IS NULL OR status != 'approved'"))
def downgrade() -> None:
    pass
