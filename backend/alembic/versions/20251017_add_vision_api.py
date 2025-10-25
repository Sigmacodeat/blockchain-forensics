"""add_vision_api

Revision ID: 20251017_add_vision_api
Revises: 20251017_add_redis_cache
Create Date: 2025-10-17 15:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_vision_api'
down_revision = '20251017_add_redis_cache'
previous_revision = '20251017_add_redis_cache'
branch_labels = None
depends_on = None


def upgrade():
    # Add Vision API columns to chat_attachments for enhanced OCR
    try:
        op.add_column('chat_attachments', sa.Column('vision_api_used', sa.String(), nullable=True))
        op.add_column('chat_attachments', sa.Column('vision_confidence', sa.Float(), nullable=True))
        op.add_column('chat_attachments', sa.Column('vision_entities', sa.JSONB(), nullable=True))
        op.add_column('chat_attachments', sa.Column('vision_processing_time', sa.Float(), nullable=True))
    except Exception:
        # Columns might already exist
        pass


def downgrade():
    try:
        op.drop_column('chat_attachments', 'vision_processing_time')
        op.drop_column('chat_attachments', 'vision_entities')
        op.drop_column('chat_attachments', 'vision_confidence')
        op.drop_column('chat_attachments', 'vision_api_used')
    except Exception:
        pass
