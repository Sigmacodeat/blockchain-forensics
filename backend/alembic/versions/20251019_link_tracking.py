"""link_tracking

Revision ID: 20251019_link_tracking
Revises: 20251019_ultimate_analytics
Create Date: 2025-10-19 18:00:00.000000

Intelligence-Grade Link-Tracking für Social-Media-Attribution
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251019_link_tracking'
down_revision = '20251019_ultimate_analytics'
branch_labels = None
depends_on = None


def upgrade():
    # Create tracked_links table
    op.create_table('tracked_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tracking_id', sa.String(), nullable=False),
        sa.Column('short_slug', sa.String(), nullable=False),
        sa.Column('short_url', sa.String(), nullable=False),
        sa.Column('target_url', sa.String(), nullable=False),
        sa.Column('source_platform', sa.String(), nullable=False),
        sa.Column('source_username', sa.String(), nullable=True),
        sa.Column('campaign', sa.String(), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_visitors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracking_id'),
        sa.UniqueConstraint('short_slug')
    )
    
    # Create indexes
    op.create_index('ix_tracked_links_tracking_id', 'tracked_links', ['tracking_id'])
    op.create_index('ix_tracked_links_short_slug', 'tracked_links', ['short_slug'])
    op.create_index('ix_tracked_links_source_platform', 'tracked_links', ['source_platform'])
    op.create_index('ix_tracked_links_source_username', 'tracked_links', ['source_username'])
    op.create_index('ix_tracked_links_campaign', 'tracked_links', ['campaign'])
    op.create_index('ix_tracked_links_created_at', 'tracked_links', ['created_at'])
    
    # Create link_clicks table
    op.create_table('link_clicks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tracking_id', sa.String(), nullable=False),
        sa.Column('intelligence_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_link_clicks_tracking_id', 'link_clicks', ['tracking_id'])
    op.create_index('ix_link_clicks_created_at', 'link_clicks', ['created_at'])


def downgrade():
    # Drop link_clicks
    op.drop_index('ix_link_clicks_created_at', table_name='link_clicks')
    op.drop_index('ix_link_clicks_tracking_id', table_name='link_clicks')
    op.drop_table('link_clicks')
    
    # Drop tracked_links
    op.drop_index('ix_tracked_links_created_at', table_name='tracked_links')
    op.drop_index('ix_tracked_links_campaign', table_name='tracked_links')
    op.drop_index('ix_tracked_links_source_username', table_name='tracked_links')
    op.drop_index('ix_tracked_links_source_platform', table_name='tracked_links')
    op.drop_index('ix_tracked_links_short_slug', table_name='tracked_links')
    op.drop_index('ix_tracked_links_tracking_id', table_name='tracked_links')
    op.drop_table('tracked_links')
