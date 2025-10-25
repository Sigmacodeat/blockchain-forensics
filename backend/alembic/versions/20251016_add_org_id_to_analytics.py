"""
Add org_id columns and indexes to web_events and web_vitals

Revision ID: 20251016_add_org_id_to_analytics
Revises: 20251015_add_sanctions_tables
Create Date: 2025-10-16 21:50:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251016_add_org_id_to_analytics"
down_revision = "20251015_add_sanctions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Add column org_id to web_events if table and column don't exist
    op.execute(sa.text(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name='web_events'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='web_events' AND column_name='org_id'
                ) THEN
                    ALTER TABLE web_events ADD COLUMN org_id VARCHAR(64);
                END IF;
            END IF;
        END$$;
        """
    ))

    # Add column org_id to web_vitals if table and column don't exist
    op.execute(sa.text(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name='web_vitals'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='web_vitals' AND column_name='org_id'
                ) THEN
                    ALTER TABLE web_vitals ADD COLUMN org_id VARCHAR(64);
                END IF;
            END IF;
        END$$;
        """
    ))

    # Create helpful indexes (if underlying tables exist)
    op.execute(sa.text(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='web_events') THEN
                EXECUTE 'CREATE INDEX IF NOT EXISTS idx_web_events_org_ts ON web_events (org_id, ts)';
                EXECUTE 'CREATE INDEX IF NOT EXISTS idx_web_events_org_event ON web_events (org_id, event)';
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='web_vitals') THEN
                EXECUTE 'CREATE INDEX IF NOT EXISTS idx_web_vitals_org_ts ON web_vitals (org_id, ts)';
            END IF;
        END$$;
        """
    ))


def downgrade() -> None:
    # Drop indexes first
    op.execute(
        sa.text(
            """
            DROP INDEX IF EXISTS idx_web_vitals_org_ts;
            DROP INDEX IF EXISTS idx_web_events_org_event;
            DROP INDEX IF EXISTS idx_web_events_org_ts;
            """
        )
    )
    # Keep columns for data retention; optional: drop columns (commented)
    # op.execute(sa.text("ALTER TABLE web_events DROP COLUMN IF EXISTS org_id"))
    # op.execute(sa.text("ALTER TABLE web_vitals DROP COLUMN IF EXISTS org_id"))
