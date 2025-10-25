"""
Add sanctions core tables: sanctioned_entity, sanctions_list_source, entity_alias, entity_list

Revision ID: 20251015_add_sanctions
Revises: 5070e8da0ae6
Create Date: 2025-10-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251015_add_sanctions'
down_revision = '5070e8da0ae6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # sources
    op.create_table(
        'sanctions_list_source',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('code', sa.String(length=16), nullable=False, index=True),
        sa.Column('version', sa.String(length=64), nullable=False),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=True),
    )

    # entities
    op.create_table(
        'sanctioned_entity',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('canonical_name', sa.String(length=512), nullable=False),
        sa.Column('canonical_name_norm', sa.String(length=512), nullable=True, index=True),
        sa.Column('type', sa.String(length=64), nullable=True),
        sa.Column('risk_level', sa.String(length=16), nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
    )

    # aliases
    op.create_table(
        'entity_alias',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('entity_id', sa.String(length=64), sa.ForeignKey('sanctioned_entity.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('value', sa.String(length=512), nullable=False),
        sa.Column('value_norm', sa.String(length=512), nullable=True, index=True),
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('source_id', sa.String(length=64), sa.ForeignKey('sanctions_list_source.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('confidence', sa.Float, nullable=True),
    )

    # entity->list relation (many-to-many)
    op.create_table(
        'entity_list',
        sa.Column('entity_id', sa.String(length=64), sa.ForeignKey('sanctioned_entity.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('list_source_id', sa.String(length=64), sa.ForeignKey('sanctions_list_source.id', ondelete='CASCADE'), primary_key=True),
    )

    # helpful indexes (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'ix_entity_alias_address_like' AND n.nspname = 'public'
            ) THEN
                CREATE INDEX ix_entity_alias_address_like ON entity_alias (value);
            END IF;
        END$$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'ix_entity_alias_value_norm' AND n.nspname = 'public'
            ) THEN
                CREATE INDEX ix_entity_alias_value_norm ON entity_alias (value_norm);
            END IF;
        END$$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'ix_sanctioned_entity_name_norm' AND n.nspname = 'public'
            ) THEN
                CREATE INDEX ix_sanctioned_entity_name_norm ON sanctioned_entity (canonical_name_norm);
            END IF;
        END$$;
    """)


def downgrade() -> None:
    op.drop_index('ix_sanctioned_entity_name_norm', table_name='sanctioned_entity')
    op.drop_index('ix_entity_alias_value_norm', table_name='entity_alias')
    op.drop_index('ix_entity_alias_address_like', table_name='entity_alias')
    op.drop_table('entity_list')
    op.drop_table('entity_alias')
    op.drop_table('sanctioned_entity')
    op.drop_table('sanctions_list_source')
