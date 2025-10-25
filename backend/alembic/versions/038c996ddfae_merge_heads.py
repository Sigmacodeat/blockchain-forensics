"""merge_heads

Revision ID: 038c996ddfae
Revises: 0fb38e61ca33, 20251019_link_tracking
Create Date: 2025-10-19 18:40:15.658656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '038c996ddfae'
down_revision: Union[str, None] = ('0fb38e61ca33', '20251019_link_tracking')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
