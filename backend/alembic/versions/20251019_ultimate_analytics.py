"""ultimate_analytics

Revision ID: 20251019_ultimate_analytics
Revises: 20251019_conversation_analytics
Create Date: 2025-10-19 17:50:00.000000

Ultimate Analytics System: Maximale Datenerfassung + KI-Auto-Optimization
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251019_ultimate_analytics'
down_revision = '20251019_conversation_analytics'
branch_labels = None
depends_on = None


def upgrade():
    # Create analytics_events table
    op.create_table('analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('fingerprint', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('behavior', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('performance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('network', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('page_url', sa.String(), nullable=False),
        sa.Column('page_title', sa.String(), nullable=True),
        sa.Column('referrer', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for analytics_events
    op.create_index('ix_analytics_events_session_id', 'analytics_events', ['session_id'])
    op.create_index('ix_analytics_events_user_id', 'analytics_events', ['user_id'])
    op.create_index('ix_analytics_events_page_url', 'analytics_events', ['page_url'])
    op.create_index('ix_analytics_events_created_at', 'analytics_events', ['created_at'])
    
    # Create ai_insights table
    op.create_table('ai_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('conversion_probability', sa.Float(), nullable=True),
        sa.Column('churn_risk', sa.Float(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('insights', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('behavior_patterns', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ai_insights
    op.create_index('ix_ai_insights_session_id', 'ai_insights', ['session_id'])
    op.create_index('ix_ai_insights_user_id', 'ai_insights', ['user_id'])
    op.create_index('ix_ai_insights_created_at', 'ai_insights', ['created_at'])
    
    # Create auto_optimizations table
    op.create_table('auto_optimizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('optimization_type', sa.String(), nullable=False),
        sa.Column('target_page', sa.String(), nullable=True),
        sa.Column('target_element', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('expected_impact', sa.String(), nullable=True),
        sa.Column('implementation_code', sa.Text(), nullable=True),
        sa.Column('ab_test_variants', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for auto_optimizations
    op.create_index('ix_auto_optimizations_status', 'auto_optimizations', ['status'])
    op.create_index('ix_auto_optimizations_priority', 'auto_optimizations', ['priority'])
    op.create_index('ix_auto_optimizations_created_at', 'auto_optimizations', ['created_at'])


def downgrade():
    # Drop auto_optimizations
    op.drop_index('ix_auto_optimizations_created_at', table_name='auto_optimizations')
    op.drop_index('ix_auto_optimizations_priority', table_name='auto_optimizations')
    op.drop_index('ix_auto_optimizations_status', table_name='auto_optimizations')
    op.drop_table('auto_optimizations')
    
    # Drop ai_insights
    op.drop_index('ix_ai_insights_created_at', table_name='ai_insights')
    op.drop_index('ix_ai_insights_user_id', table_name='ai_insights')
    op.drop_index('ix_ai_insights_session_id', table_name='ai_insights')
    op.drop_table('ai_insights')
    
    # Drop analytics_events
    op.drop_index('ix_analytics_events_created_at', table_name='analytics_events')
    op.drop_index('ix_analytics_events_page_url', table_name='analytics_events')
    op.drop_index('ix_analytics_events_user_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_session_id', table_name='analytics_events')
    op.drop_table('analytics_events')
