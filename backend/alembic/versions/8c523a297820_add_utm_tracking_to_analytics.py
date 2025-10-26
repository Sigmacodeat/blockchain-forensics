"""add_utm_tracking_to_analytics

Revision ID: 8c523a297820
Revises: c40f64d42986
Create Date: 2025-10-26 09:00:47.395944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c523a297820'
down_revision: Union[str, None] = 'c40f64d42986'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add UTM tracking columns to analytics_events table
    op.add_column('analytics_events', sa.Column('utm_source', sa.String(), nullable=True))
    op.add_column('analytics_events', sa.Column('utm_medium', sa.String(), nullable=True))
    op.add_column('analytics_events', sa.Column('utm_campaign', sa.String(), nullable=True))
    op.add_column('analytics_events', sa.Column('utm_term', sa.String(), nullable=True))
    op.add_column('analytics_events', sa.Column('utm_content', sa.String(), nullable=True))
    op.add_column('analytics_events', sa.Column('social_source', sa.String(), nullable=True))

    # Create indexes for UTM columns for better query performance
    op.create_index('ix_analytics_events_utm_source', 'analytics_events', ['utm_source'])
    op.create_index('ix_analytics_events_utm_medium', 'analytics_events', ['utm_medium'])
    op.create_index('ix_analytics_events_utm_campaign', 'analytics_events', ['utm_campaign'])
    op.create_index('ix_analytics_events_social_source', 'analytics_events', ['social_source'])


def downgrade() -> None:
    # Drop UTM indexes
    op.drop_index('ix_analytics_events_social_source', table_name='analytics_events')
    op.drop_index('ix_analytics_events_utm_campaign', table_name='analytics_events')
    op.drop_index('ix_analytics_events_utm_medium', table_name='analytics_events')
    op.drop_index('ix_analytics_events_utm_source', table_name='analytics_events')

    # Drop UTM columns
    op.drop_column('analytics_events', 'social_source')
    op.drop_column('analytics_events', 'utm_content')
    op.drop_column('analytics_events', 'utm_term')
    op.drop_column('analytics_events', 'utm_campaign')
    op.drop_column('analytics_events', 'utm_medium')
    op.drop_column('analytics_events', 'utm_source')
