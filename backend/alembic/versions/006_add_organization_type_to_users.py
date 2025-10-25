"""Add organization organization & verification fields to users

Revision ID: 20251021_add_user_org_fields
Revises: 20251020_partner_affiliate
Create Date: 2025-10-24 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251021_add_user_org_fields'
down_revision = '20251020_partner_affiliate'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('organization_type', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('organization_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('institutional_discount_requested', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
    op.add_column('users', sa.Column('institutional_discount_verified', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
    op.add_column('users', sa.Column('verification_status', sa.String(length=32), nullable=False, server_default='none'))
    op.add_column('users', sa.Column('verification_documents', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('verification_notes', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('verified_by', sa.String(length=64), nullable=True))
    op.create_foreign_key(
        'users_verified_by_fkey',
        'users',
        'users',
        ['verified_by'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('users_verified_by_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'verified_by')
    op.drop_column('users', 'verified_at')
    op.drop_column('users', 'verification_notes')
    op.drop_column('users', 'verification_documents')
    op.drop_column('users', 'verification_status')
    op.drop_column('users', 'institutional_discount_verified')
    op.drop_column('users', 'institutional_discount_requested')
    op.drop_column('users', 'organization_name')
    op.drop_column('users', 'organization_type')
