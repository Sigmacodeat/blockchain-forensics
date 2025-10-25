"""add_ocr_service

Revision ID: 20251017_add_ocr_service
Revises: 20251017_add_chat_attachments
Create Date: 2025-10-17 15:39:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_ocr_service'
down_revision = '20251017_add_chat_attachments'
previous_revision = '20251017_add_chat_attachments'
branch_labels = None
depends_on = None


def upgrade():
    # Add OCR-specific columns to chat_attachments if not exists
    try:
        op.add_column('chat_attachments', sa.Column('ocr_status', sa.String(), nullable=True))
        op.add_column('chat_attachments', sa.Column('ocr_text', sa.Text(), nullable=True))
        op.add_column('chat_attachments', sa.Column('ocr_confidence', sa.Float(), nullable=True))
        op.add_column('chat_attachments', sa.Column('ocr_processing_time', sa.Float(), nullable=True))
    except Exception:
        # Columns might already exist
        pass


def downgrade():
    try:
        op.drop_column('chat_attachments', 'ocr_processing_time')
        op.drop_column('chat_attachments', 'ocr_confidence')
        op.drop_column('chat_attachments', 'ocr_text')
        op.drop_column('chat_attachments', 'ocr_status')
    except Exception:
        pass
