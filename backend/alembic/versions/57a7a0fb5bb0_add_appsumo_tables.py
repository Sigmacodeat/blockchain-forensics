"""add_appsumo_tables

Revision ID: 57a7a0fb5bb0
Revises: 038c996ddfae
Create Date: 2025-10-19 18:40:30.397227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '57a7a0fb5bb0'
down_revision: Union[str, None] = '038c996ddfae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ======================================
    # 1. APPSUMO_CODES TABLE
    # ======================================
    op.create_table(
        'appsumo_codes',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('product', sa.String(50), nullable=False),
        sa.Column('tier', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('redeemed_at', sa.DateTime(), nullable=True),
        sa.Column('redeemed_by_user_id', postgresql.UUID(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('batch_id', sa.String(50), nullable=True),
        sa.Column('appsumo_order_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_appsumo_codes_code'),
        sa.ForeignKeyConstraint(['redeemed_by_user_id'], ['users.id'], name='fk_appsumo_codes_user')
    )
    op.create_index('idx_appsumo_codes_code', 'appsumo_codes', ['code'])
    op.create_index('idx_appsumo_codes_product', 'appsumo_codes', ['product'])
    op.create_index('idx_appsumo_codes_status', 'appsumo_codes', ['status'])
    
    # ======================================
    # 2. USER_PRODUCTS TABLE
    # ======================================
    op.create_table(
        'user_products',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('product', sa.String(50), nullable=False),
        sa.Column('tier', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('appsumo_code', sa.String(100), nullable=True),
        sa.Column('appsumo_purchase_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('activated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('features', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('limits', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_products_user', ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'product', name='uq_user_products_user_product')
    )
    op.create_index('idx_user_products_user', 'user_products', ['user_id'])
    op.create_index('idx_user_products_product', 'user_products', ['product'])
    op.create_index('idx_user_products_status', 'user_products', ['status'])
    
    # ======================================
    # 3. APPSUMO_METRICS TABLE
    # ======================================
    op.create_table(
        'appsumo_metrics',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('product', sa.String(50), nullable=False),
        sa.Column('codes_redeemed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_users', sa.Integer(), server_default='0', nullable=False),
        sa.Column('revenue_cents', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('commission_cents', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('net_revenue_cents', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('tier_1_redemptions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tier_2_redemptions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tier_3_redemptions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'product', name='uq_appsumo_metrics_date_product')
    )
    op.create_index('idx_appsumo_metrics_date', 'appsumo_metrics', ['date'])
    op.create_index('idx_appsumo_metrics_product', 'appsumo_metrics', ['product'])


def downgrade() -> None:
    # Drop in reverse order
    op.drop_table('appsumo_metrics')
    op.drop_table('user_products')
    op.drop_table('appsumo_codes')
