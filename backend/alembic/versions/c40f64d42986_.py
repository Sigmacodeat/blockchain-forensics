"""empty message

Revision ID: c40f64d42986
Revises: 006, c1_transactions_table
Create Date: 2025-10-24 15:26:50.593135

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'c40f64d42986'
down_revision: Union[str, None] = ('20251021_add_user_org_fields', 'c1_transactions_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
