"""add_kb_metadata

Revision ID: 20251017_add_kb_metadata
Revises: ea80754af4e5
Create Date: 2025-10-17 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_kb_metadata'
down_revision = 'ea80754af4e5'
previous_revision = 'ea80754af4e5'
branch_labels = None
depends_on = None


def upgrade():
    # Add metadata column to kb_docs (JSONB available in PG >=9.4)
    try:
        jsonb_type = sa.dialects.postgresql.JSONB  # type: ignore
    except Exception:
        jsonb_type = sa.JSON
    op.add_column('kb_docs', sa.Column('metadata', jsonb_type(), nullable=True))

    # Create kb_embeddings with generic ARRAY of FLOATs (portable)
    op.create_table(
        'kb_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.ARRAY(sa.Float()), nullable=False),
        sa.ForeignKeyConstraint(['doc_id'], ['kb_docs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Try to create a specialized index if pgvector/operator class is available
    try:
        # This may fail if pgvector is not installed; keep migration robust
        op.execute("CREATE INDEX IF NOT EXISTS ix_kb_embeddings_embedding ON kb_embeddings USING ivfflat (embedding);")
    except Exception:
        # Fallback: simple GIN/GIST is not applicable to float arrays; skip specialized index
        pass

    # Add index for metadata source (expression index)
    try:
        op.execute("CREATE INDEX IF NOT EXISTS ix_kb_docs_metadata_source ON kb_docs ((metadata->>'source'));")
    except Exception:
        pass


def downgrade():
    try:
        op.execute("DROP INDEX IF EXISTS ix_kb_docs_metadata_source;")
    except Exception:
        pass
    try:
        op.execute("DROP INDEX IF EXISTS ix_kb_embeddings_embedding;")
    except Exception:
        pass
    op.drop_table('kb_embeddings')
    try:
        op.drop_column('kb_docs', 'metadata')
    except Exception:
        pass
