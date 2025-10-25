"""add_chat_feedback

Revision ID: 20251017_add_chat_feedback
Revises: 20251017_add_chat_history
Create Date: 2025-10-17 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_chat_feedback'
down_revision = '20251017_add_chat_history'
previous_revision = '20251017_add_chat_history'
branch_labels = None
depends_on = None


def upgrade():
    # Create chat_feedback table for CSAT and analytics
    op.create_table('chat_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('helpful', sa.Boolean(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for performance
    op.create_index('ix_chat_feedback_session_id', 'chat_feedback', ['session_id'])
    op.create_index('ix_chat_feedback_message_id', 'chat_feedback', ['message_id'])
    op.create_index('ix_chat_feedback_timestamp', 'chat_feedback', ['timestamp'])


def downgrade():
    op.drop_index('ix_chat_feedback_timestamp', table_name='chat_feedback')
    op.drop_index('ix_chat_feedback_message_id', table_name='chat_feedback')
    op.drop_index('ix_chat_feedback_session_id', table_name='chat_feedback')
    op.drop_table('chat_feedback')
