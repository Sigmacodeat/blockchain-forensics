"""add last_login to users

Revision ID: b1_add_last_login
Revises: 57a7a0fb5bb0
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1_add_last_login'
down_revision = '57a7a0fb5bb0'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_login column if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'last_login'
            ) THEN
                ALTER TABLE users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """)


def downgrade():
    op.drop_column('users', 'last_login')
