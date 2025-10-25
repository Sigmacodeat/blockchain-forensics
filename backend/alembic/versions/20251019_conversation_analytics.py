"""conversation_analytics

Revision ID: 20251019_conversation_analytics
Revises: <previous_revision>
Create Date: 2025-10-19 17:35:00.000000

Erweitert chat_sessions mit User-Identity-Resolution & Attribution
Fügt conversation_events für Funnel-Tracking hinzu
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251019_conversation_analytics'
down_revision = '20251017_add_chat_history'  # Adjust based on your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Extend chat_sessions table
    op.add_column('chat_sessions', sa.Column('anonymous_id', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('fingerprint', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('utm_source', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('utm_medium', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('utm_campaign', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('utm_term', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('utm_content', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('referrer', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('language', sa.String(), nullable=True, server_default='en'))
    
    # Create indexes
    op.create_index('ix_chat_sessions_anonymous_id', 'chat_sessions', ['anonymous_id'])
    
    # Create conversation_events table
    op.create_table('conversation_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('anonymous_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_data', sa.JSONB(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for conversation_events
    op.create_index('ix_conversation_events_session_id', 'conversation_events', ['session_id'])
    op.create_index('ix_conversation_events_user_id', 'conversation_events', ['user_id'])
    op.create_index('ix_conversation_events_anonymous_id', 'conversation_events', ['anonymous_id'])
    op.create_index('ix_conversation_events_event_type', 'conversation_events', ['event_type'])
    op.create_index('ix_conversation_events_timestamp', 'conversation_events', ['timestamp'])


def downgrade():
    # Drop conversation_events
    op.drop_index('ix_conversation_events_timestamp', table_name='conversation_events')
    op.drop_index('ix_conversation_events_event_type', table_name='conversation_events')
    op.drop_index('ix_conversation_events_anonymous_id', table_name='conversation_events')
    op.drop_index('ix_conversation_events_user_id', table_name='conversation_events')
    op.drop_index('ix_conversation_events_session_id', table_name='conversation_events')
    op.drop_table('conversation_events')
    
    # Drop chat_sessions extensions
    op.drop_index('ix_chat_sessions_anonymous_id', table_name='chat_sessions')
    op.drop_column('chat_sessions', 'language')
    op.drop_column('chat_sessions', 'referrer')
    op.drop_column('chat_sessions', 'utm_content')
    op.drop_column('chat_sessions', 'utm_term')
    op.drop_column('chat_sessions', 'utm_campaign')
    op.drop_column('chat_sessions', 'utm_medium')
    op.drop_column('chat_sessions', 'utm_source')
    op.drop_column('chat_sessions', 'fingerprint')
    op.drop_column('chat_sessions', 'anonymous_id')
