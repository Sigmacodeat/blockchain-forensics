"""add_alert_annotations

Revision ID: 5070e8da0ae6
Revises: ea80754af4e5
Create Date: 2025-10-14 12:19:10.440972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5070e8da0ae6'
down_revision: Union[str, None] = 'ea80754af4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('alert_annotations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.String(length=128), nullable=False),
        sa.Column('disposition', sa.String(length=32), nullable=True),
        sa.Column('event_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_annotations_alert_id'), 'alert_annotations', ['alert_id'], unique=False)
    op.create_index(op.f('ix_alert_annotations_updated_at'), 'alert_annotations', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_alert_annotations_updated_at'), table_name='alert_annotations')
    op.drop_index(op.f('ix_alert_annotations_alert_id'), table_name='alert_annotations')
    op.drop_table('alert_annotations')
