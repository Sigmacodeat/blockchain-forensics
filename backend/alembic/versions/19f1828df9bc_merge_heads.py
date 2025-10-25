"""merge heads

Revision ID: 19f1828df9bc
Revises: 20251017_add_vision_api, 20251019_update_chat_feedback_schema
Create Date: 2025-10-19 14:20:23.509471

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '19f1828df9bc'
down_revision: Union[str, None] = ('20251017_add_vision_api', '20251019_update_chat_feedback_schema')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
