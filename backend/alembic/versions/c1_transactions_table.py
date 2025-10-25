"""create transactions table for trace storage

Revision ID: c1_transactions_table
Revises: b1_add_last_login
Create Date: 2025-10-20

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'c1_transactions_table'
down_revision = 'b1_add_last_login'
branch_labels = None
depends_on = None


def upgrade():
    # Create transactions table for trace storage
    op.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tx_hash VARCHAR(255) NOT NULL,
            chain VARCHAR(50) NOT NULL,
            block_number BIGINT,
            block_timestamp TIMESTAMP WITH TIME ZONE,
            from_address VARCHAR(255) NOT NULL,
            to_address VARCHAR(255),
            value DECIMAL(78, 0),  -- Support large numbers (wei)
            gas_price DECIMAL(78, 0),
            gas_used INTEGER,
            input_data TEXT,
            status SMALLINT,  -- 0=failed, 1=success
            contract_address VARCHAR(255),
            token_transfers JSONB DEFAULT '[]',
            internal_transactions JSONB DEFAULT '[]',
            logs JSONB DEFAULT '[]',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Constraints
            UNIQUE(tx_hash, chain)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_transactions_tx_hash ON transactions(tx_hash);
        CREATE INDEX IF NOT EXISTS idx_transactions_chain ON transactions(chain);
        CREATE INDEX IF NOT EXISTS idx_transactions_from_address ON transactions(from_address);
        CREATE INDEX IF NOT EXISTS idx_transactions_to_address ON transactions(to_address);
        CREATE INDEX IF NOT EXISTS idx_transactions_block_number ON transactions(block_number);
        CREATE INDEX IF NOT EXISTS idx_transactions_block_timestamp ON transactions(block_timestamp);
        CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
        
        -- Composite indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_transactions_chain_from ON transactions(chain, from_address);
        CREATE INDEX IF NOT EXISTS idx_transactions_chain_to ON transactions(chain, to_address);
        CREATE INDEX IF NOT EXISTS idx_transactions_chain_block ON transactions(chain, block_number);
        
        -- GIN index for JSONB columns
        CREATE INDEX IF NOT EXISTS idx_transactions_token_transfers_gin ON transactions USING GIN(token_transfers);
        CREATE INDEX IF NOT EXISTS idx_transactions_metadata_gin ON transactions USING GIN(metadata);
        
        -- Update trigger for updated_at
        CREATE OR REPLACE FUNCTION update_transactions_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS transactions_updated_at_trigger ON transactions;
        CREATE TRIGGER transactions_updated_at_trigger
            BEFORE UPDATE ON transactions
            FOR EACH ROW
            EXECUTE FUNCTION update_transactions_updated_at();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS transactions_updated_at_trigger ON transactions;")
    op.execute("DROP FUNCTION IF EXISTS update_transactions_updated_at;")
    op.execute("DROP TABLE IF EXISTS transactions;")
