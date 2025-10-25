"""update_chat_feedback_schema

Revision ID: 20251019_update_chat_feedback_schema
Revises: 20251018_add_user_subscription_fields
Create Date: 2025-10-19 08:00:00.000000

Updates chat_feedback table for new Thumbs Up/Down system
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251019_update_chat_feedback_schema'
down_revision = '20251018_subscription'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure chat_feedback table exists (minimal schema if missing)
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.tables WHERE table_name='chat_feedback'
                ) THEN
                    CREATE TABLE chat_feedback (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR,
                        message_id INTEGER,
                        helpful BOOLEAN,
                        note TEXT,
                        timestamp TIMESTAMP DEFAULT now()
                    );
                END IF;
            END$$;
            """
        )
    )

    # Add new columns with IF NOT EXISTS
    op.execute(sa.text("ALTER TABLE chat_feedback ADD COLUMN IF NOT EXISTS user_id INTEGER"))
    op.execute(sa.text("ALTER TABLE chat_feedback ADD COLUMN IF NOT EXISTS message_index INTEGER"))
    op.execute(sa.text("ALTER TABLE chat_feedback ADD COLUMN IF NOT EXISTS message_content TEXT"))
    # Create enum type if not exists, then add column if not exists
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedbacktype') THEN
                    CREATE TYPE feedbacktype AS ENUM ('positive','negative');
                END IF;
            END$$;
            """
        )
    )
    op.execute(sa.text("ALTER TABLE chat_feedback ADD COLUMN IF NOT EXISTS feedback_type feedbacktype"))
    op.execute(sa.text("ALTER TABLE chat_feedback ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now()"))

    # Create foreign key to users table if it exists
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='users') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.constraint_column_usage
                        WHERE table_name='chat_feedback' AND constraint_name='fk_chat_feedback_user_id'
                    ) THEN
                        ALTER TABLE chat_feedback
                        ADD CONSTRAINT fk_chat_feedback_user_id
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                    END IF;
                END IF;
            END$$;
            """
        )
    )

    # Create indices for new columns if not exist
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_chat_feedback_user_id ON chat_feedback (user_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_chat_feedback_feedback_type ON chat_feedback (feedback_type)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_chat_feedback_created_at ON chat_feedback (created_at)"))
    
    # Drop old columns that we don't need anymore (optional - keep for backwards compatibility)
    # op.drop_column('chat_feedback', 'helpful')
    # op.drop_column('chat_feedback', 'note')
    # op.drop_column('chat_feedback', 'message_id')


def downgrade():
    # Drop new indices
    op.drop_index('ix_chat_feedback_created_at', table_name='chat_feedback')
    op.drop_index('ix_chat_feedback_feedback_type', table_name='chat_feedback')
    op.drop_index('ix_chat_feedback_user_id', table_name='chat_feedback')
    
    # Drop foreign key
    try:
        op.drop_constraint('fk_chat_feedback_user_id', 'chat_feedback', type_='foreignkey')
    except:
        pass
    
    # Drop new columns
    op.drop_column('chat_feedback', 'created_at')
    op.drop_column('chat_feedback', 'feedback_type')
    op.drop_column('chat_feedback', 'message_content')
    op.drop_column('chat_feedback', 'message_index')
    op.drop_column('chat_feedback', 'user_id')
