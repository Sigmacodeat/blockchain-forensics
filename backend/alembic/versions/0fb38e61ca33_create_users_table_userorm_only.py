"""create users table (UserORM only)

Revision ID: 0fb38e61ca33
Revises: 19f1828df9bc
Create Date: 2025-10-19 14:29:04.527583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fb38e61ca33'
down_revision: Union[str, None] = '19f1828df9bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table according to UserORM, guarded for idempotency
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.tables WHERE table_name='users'
                ) THEN
                    CREATE TABLE users (
                        id VARCHAR(64) PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        username VARCHAR(100) NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        role VARCHAR(32) NOT NULL DEFAULT 'viewer',
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        plan VARCHAR(32) NOT NULL DEFAULT 'community',
                        features JSON NOT NULL DEFAULT '[]',
                        organization VARCHAR(255)
                    );
                    CREATE UNIQUE INDEX ix_users_email ON users(email);
                    CREATE UNIQUE INDEX ix_users_username ON users(username);
                    CREATE INDEX ix_users_id ON users(id);
                ELSE
                    -- Ensure required columns exist (for partially created tables)
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='username') THEN
                        ALTER TABLE users ADD COLUMN username VARCHAR(100) NOT NULL DEFAULT '';
                        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users(username);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role') THEN
                        ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'viewer';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_active') THEN
                        ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='updated_at') THEN
                        ALTER TABLE users ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='plan') THEN
                        ALTER TABLE users ADD COLUMN plan VARCHAR(32) NOT NULL DEFAULT 'community';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='features') THEN
                        ALTER TABLE users ADD COLUMN features JSON NOT NULL DEFAULT '[]';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='organization') THEN
                        ALTER TABLE users ADD COLUMN organization VARCHAR(255);
                    END IF;
                    -- Ensure indexes
                    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);
                    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users(username);
                    CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);
                END IF;
            END$$;
            """
        )
    )


def downgrade() -> None:
    # Drop indexes and users table if exists
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='users') THEN
                    DROP INDEX IF EXISTS ix_users_id;
                    DROP INDEX IF EXISTS ix_users_username;
                    DROP INDEX IF EXISTS ix_users_email;
                    DROP TABLE IF EXISTS users;
                END IF;
            END$$;
            """
        )
    )
