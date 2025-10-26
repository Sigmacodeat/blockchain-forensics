"""add_social_media_source_to_analytics

Revision ID: 976ac944b36c
Revises: 8c523a297820
Create Date: 2025-10-26 09:12:44.352099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '976ac944b36c'
down_revision: Union[str, None] = '8c523a297820'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
