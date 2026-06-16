"""data_migration_promote_johndoe_to_admin

Revision ID: 5dc2d8990f0b
Revises: e0c19bacdafb
Create Date: 2026-06-16 14:24:17.222928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5dc2d8990f0b'
down_revision: Union[str, None] = 'e0c19bacdafb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import uuid

def upgrade() -> None:
    conn = op.get_bind()
    res = conn.execute(sa.text("SELECT first_name, middle_name, last_name, email, hashed_password FROM partner_users WHERE email IN ('johndoe@gmail.com', 'chijindu.nwokeohuru@gmail.com')"))
    partners = res.fetchall()
    
    for p in partners:
        # Check if already in users
        existing = conn.execute(sa.text("SELECT id FROM users WHERE email = :email"), {"email": p[3]}).fetchone()
        if existing:
            conn.execute(sa.text("UPDATE users SET user_type = 'SUPERADMINISTRATOR' WHERE email = :email"), {"email": p[3]})
        else:
            new_id = str(uuid.uuid4())
            user_name = f"johndoe_admin_{new_id[:8]}"
            conn.execute(sa.text("""
                INSERT INTO users (
                    id, first_name, middle_name, last_name, user_name, email, 
                    hashed_password, user_type, is_active, is_password_changed, date_joined
                ) VALUES (
                    :id, :first_name, :middle_name, :last_name, :user_name, :email, 
                    :hashed_password, 'SUPERADMINISTRATOR', true, false, now()
                )
            """), {
                "id": new_id,
                "first_name": p[0],
                "middle_name": p[1] or "",
                "last_name": p[2],
                "user_name": user_name,
                "email": p[3],
                "hashed_password": p[4]
            })

def downgrade() -> None:
    pass
