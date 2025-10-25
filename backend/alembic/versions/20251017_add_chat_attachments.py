"""add_chat_attachments

Revision ID: 20251017_add_chat_attachments
Revises: 20251017_add_chat_feedback
Create Date: 2025-10-17 15:34:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_chat_attachments'
down_revision = '20251017_add_chat_feedback'
previous_revision = '20251017_add_chat_feedback'
branch_labels = None
depends_on = None


def upgrade():
    # Create chat_attachments table for multimodal uploads
    op.create_table('chat_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),  # Path in storage (local/S3)
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),  # Extracted text from OCR/Vision
        sa.Column('metadata', sa.JSONB(), nullable=True),  # Additional metadata (entities, etc.)
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for performance
    op.create_index('ix_chat_attachments_session_id', 'chat_attachments', ['session_id'])
    op.create_index('ix_chat_attachments_message_id', 'chat_attachments', ['message_id'])
    op.create_index('ix_chat_attachments_uploaded_at', 'chat_attachments', ['uploaded_at'])


def downgrade():
    op.drop_index('ix_chat_attachments_uploaded_at', table_name='chat_attachments')
    op.drop_index('ix_chat_attachments_message_id', table_name='chat_attachments')
    op.drop_index('ix_chat_attachments_session_id', table_name='chat_attachments')
    op.drop_table('chat_attachments')
