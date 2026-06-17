"""update_chijindu_partner_user_type

Revision ID: 8bd595b1e036
Revises: 5dc2d8990f0b
Create Date: 2026-06-17 12:10:17.051550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bd595b1e036'
down_revision: Union[str, None] = '5dc2d8990f0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE partner_users 
        SET user_type = 'SUPERADMINISTRATOR' 
        WHERE email IN ('chijindu.nwokeohuru@gmail.com', 'johndoe@gmail.com')
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE partner_users 
        SET user_type = NULL 
        WHERE email IN ('chijindu.nwokeohuru@gmail.com', 'johndoe@gmail.com')
    """))
