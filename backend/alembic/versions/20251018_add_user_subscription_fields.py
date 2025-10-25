"""Add user subscription fields

Revision ID: 20251018_subscription
Revises: previous_revision
Create Date: 2025-10-18 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20251018_subscription'
down_revision = '20251016_add_org_id_to_analytics'
branch_labels = None
depends_on = None


def upgrade():
    """Add subscription-related fields to users table"""
    
    # Add plan enum if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionplan') THEN
                CREATE TYPE subscriptionplan AS ENUM (
                    'community', 'starter', 'pro', 'business', 'plus', 'enterprise'
                );
            END IF;
        END$$;
    """)
    
    # Add subscription status enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus') THEN
                CREATE TYPE subscriptionstatus AS ENUM (
                    'none', 'active', 'past_due', 'cancelling', 'cancelled'
                );
            END IF;
        END$$;
    """)
    
    # Add columns to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Plan column with default 'community'
        batch_op.add_column(
            sa.Column('plan', sa.Enum('community', 'starter', 'pro', 'business', 'plus', 'enterprise', name='subscriptionplan'), 
                     nullable=False, server_default='community')
        )
        
        # Subscription status with default 'none'
        batch_op.add_column(
            sa.Column('subscription_status', sa.Enum('none', 'active', 'past_due', 'cancelling', 'cancelled', name='subscriptionstatus'),
                     nullable=False, server_default='none')
        )
        
        # Stripe IDs
        batch_op.add_column(
            sa.Column('subscription_id', sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column('stripe_customer_id', sa.String(length=255), nullable=True)
        )
        
        # Billing cycle dates
        batch_op.add_column(
            sa.Column('billing_cycle_start', sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('billing_cycle_end', sa.DateTime(), nullable=True)
        )
        
        # Add indices for performance
        batch_op.create_index('idx_users_plan', ['plan'])
        batch_op.create_index('idx_users_subscription_status', ['subscription_status'])
        batch_op.create_index('idx_users_stripe_customer_id', ['stripe_customer_id'])


def downgrade():
    """Remove subscription fields"""
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Drop indices
        batch_op.drop_index('idx_users_stripe_customer_id')
        batch_op.drop_index('idx_users_subscription_status')
        batch_op.drop_index('idx_users_plan')
        
        # Drop columns
        batch_op.drop_column('billing_cycle_end')
        batch_op.drop_column('billing_cycle_start')
        batch_op.drop_column('stripe_customer_id')
        batch_op.drop_column('subscription_id')
        batch_op.drop_column('subscription_status')
        batch_op.drop_column('plan')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS subscriptionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS subscriptionplan CASCADE")
