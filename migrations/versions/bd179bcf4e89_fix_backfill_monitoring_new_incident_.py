"""fix: backfill monitoring new incident fields with zeros

Revision ID: bd179bcf4e89
Revises: ef61c491c72e
Create Date: 2026-07-13 14:35:30.979219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd179bcf4e89'
down_revision: Union[str, None] = 'ef61c491c72e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE monitoring 
        SET 
            paediatric_over_5 = COALESCE(paediatric_over_5, 0),
            drowning = COALESCE(drowning, 0),
            snake_bite = COALESCE(snake_bite, 0),
            other_weapons = COALESCE(other_weapons, 0),
            gunshot = COALESCE(gunshot, 0),
            others = COALESCE(others, 0),
            paediatric_under_5 = COALESCE(paediatric_under_5, 0),
            neonatal_under_5 = COALESCE(neonatal_under_5, 0),
            obstetric_accident = COALESCE(obstetric_accident, 0),
            rta = COALESCE(rta, 0),
            bemonc = COALESCE(bemonc, 0),
            cemonc = COALESCE(cemonc, 0),
            maternal_mortalities = COALESCE(maternal_mortalities, 0),
            neonatal_mortalities = COALESCE(neonatal_mortalities, 0)
    """)


def downgrade() -> None:
    pass
