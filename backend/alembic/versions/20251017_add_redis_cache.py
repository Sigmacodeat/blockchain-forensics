"""add_redis_cache

Revision ID: 20251017_add_redis_cache
Revises: 20251017_add_ocr_service
Create Date: 2025-10-17 15:41:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_redis_cache'
down_revision = '20251017_add_ocr_service'
previous_revision = '20251017_add_ocr_service'
branch_labels = None
depends_on = None


def upgrade():
    # Add cache metadata columns to chat_attachments for Redis integration
    try:
        op.add_column('chat_attachments', sa.Column('cache_key', sa.String(), nullable=True))
        op.add_column('chat_attachments', sa.Column('cache_ttl', sa.Integer(), nullable=True))
        op.add_column('chat_attachments', sa.Column('cache_hits', sa.Integer(), nullable=True, server_default='0'))
    except Exception:
        # Columns might already exist
        pass


def downgrade():
    try:
        op.drop_column('chat_attachments', 'cache_hits')
        op.drop_column('chat_attachments', 'cache_ttl')
        op.drop_column('chat_attachments', 'cache_key')
    except Exception:
        pass
