-- OFAC Sanctions Database Schema
-- Stores SDN (Specially Designated Nationals) list and crypto addresses

-- SDN Entities Table
CREATE TABLE IF NOT EXISTS ofac_sdn_entities (
    entity_number VARCHAR(20) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(50),
    program VARCHAR(200),
    title VARCHAR(200),
    remarks TEXT,
    source VARCHAR(50) NOT NULL DEFAULT 'OFAC_SDN',
    list_type VARCHAR(50) NOT NULL DEFAULT 'sanctions',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for SDN entities
CREATE INDEX IF NOT EXISTS idx_sdn_name ON ofac_sdn_entities(LOWER(name));
CREATE INDEX IF NOT EXISTS idx_sdn_program ON ofac_sdn_entities(program);
CREATE INDEX IF NOT EXISTS idx_sdn_type ON ofac_sdn_entities(entity_type);

-- Full-text search index (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_sdn_name_fts ON ofac_sdn_entities USING GIN(to_tsvector('english', name));


-- Alternate Names Table
CREATE TABLE IF NOT EXISTS ofac_alt_names (
    id SERIAL PRIMARY KEY,
    entity_number VARCHAR(20) NOT NULL,
    alt_number VARCHAR(20) NOT NULL,
    alt_type VARCHAR(50),
    alt_name VARCHAR(500) NOT NULL,
    remarks TEXT,
    source VARCHAR(50) NOT NULL DEFAULT 'OFAC_ALT',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (entity_number) REFERENCES ofac_sdn_entities(entity_number) ON DELETE CASCADE,
    UNIQUE(entity_number, alt_number)
);

-- Indexes for alternate names
CREATE INDEX IF NOT EXISTS idx_alt_name ON ofac_alt_names(LOWER(alt_name));
CREATE INDEX IF NOT EXISTS idx_alt_entity ON ofac_alt_names(entity_number);


-- Addresses Table (physical + crypto)
CREATE TABLE IF NOT EXISTS ofac_addresses (
    id SERIAL PRIMARY KEY,
    entity_number VARCHAR(20) NOT NULL,
    address_number VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    city_state VARCHAR(200),
    country VARCHAR(100),
    remarks TEXT,
    is_crypto BOOLEAN NOT NULL DEFAULT FALSE,
    crypto_address VARCHAR(100),
    source VARCHAR(50) NOT NULL DEFAULT 'OFAC_ADD',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (entity_number) REFERENCES ofac_sdn_entities(entity_number) ON DELETE CASCADE,
    UNIQUE(entity_number, address_number)
);

-- Indexes for addresses
CREATE INDEX IF NOT EXISTS idx_addr_entity ON ofac_addresses(entity_number);
CREATE INDEX IF NOT EXISTS idx_addr_crypto ON ofac_addresses(is_crypto, crypto_address);


-- Sanctioned Crypto Addresses Table (for fast O(1) lookup)
CREATE TABLE IF NOT EXISTS sanctioned_addresses (
    address VARCHAR(100) PRIMARY KEY,
    entity_number VARCHAR(20),
    chain VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'OFAC',
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (entity_number) REFERENCES ofac_sdn_entities(entity_number) ON DELETE CASCADE
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_sanctioned_chain ON sanctioned_addresses(chain);
CREATE INDEX IF NOT EXISTS idx_sanctioned_entity ON sanctioned_addresses(entity_number);


-- Sanctions Update Log
CREATE TABLE IF NOT EXISTS sanctions_updates (
    id SERIAL PRIMARY KEY,
    update_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    sdn_count INTEGER NOT NULL DEFAULT 0,
    alt_names_count INTEGER NOT NULL DEFAULT 0,
    addresses_count INTEGER NOT NULL DEFAULT 0,
    crypto_addresses INTEGER NOT NULL DEFAULT 0,
    duration_seconds FLOAT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    errors TEXT[]
);

-- Index for update history
CREATE INDEX IF NOT EXISTS idx_updates_timestamp ON sanctions_updates(update_timestamp DESC);


-- Screening Results Table (audit trail)
CREATE TABLE IF NOT EXISTS screening_results (
    id SERIAL PRIMARY KEY,
    screened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    screen_type VARCHAR(50) NOT NULL, -- 'address', 'name', 'entity'
    query_value TEXT NOT NULL,
    is_match BOOLEAN NOT NULL DEFAULT FALSE,
    confidence FLOAT,
    match_type VARCHAR(50),
    entity_number VARCHAR(20),
    matched_name VARCHAR(500),
    risk_level VARCHAR(20),
    action_taken VARCHAR(50),
    user_id INTEGER,
    case_id VARCHAR(100),
    metadata JSONB,
    FOREIGN KEY (entity_number) REFERENCES ofac_sdn_entities(entity_number) ON DELETE SET NULL
);

-- Indexes for screening results
CREATE INDEX IF NOT EXISTS idx_screening_timestamp ON screening_results(screened_at DESC);
CREATE INDEX IF NOT EXISTS idx_screening_type ON screening_results(screen_type);
CREATE INDEX IF NOT EXISTS idx_screening_match ON screening_results(is_match, risk_level);
CREATE INDEX IF NOT EXISTS idx_screening_entity ON screening_results(entity_number);


-- Compliance Actions Table
CREATE TABLE IF NOT EXISTS compliance_actions (
    id SERIAL PRIMARY KEY,
    action_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    action_type VARCHAR(50) NOT NULL, -- 'FREEZE', 'BLOCK', 'FLAG', 'REPORT'
    address VARCHAR(100),
    entity_number VARCHAR(20),
    reason TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    initiated_by INTEGER,
    approved_by INTEGER,
    approved_at TIMESTAMP,
    case_reference VARCHAR(100),
    metadata JSONB,
    FOREIGN KEY (entity_number) REFERENCES ofac_sdn_entities(entity_number) ON DELETE SET NULL
);

-- Indexes for compliance actions
CREATE INDEX IF NOT EXISTS idx_compliance_timestamp ON compliance_actions(action_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_compliance_type ON compliance_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_compliance_status ON compliance_actions(status);
CREATE INDEX IF NOT EXISTS idx_compliance_address ON compliance_actions(address);


-- Statistics View
CREATE OR REPLACE VIEW sanctions_statistics AS
SELECT
    (SELECT COUNT(*) FROM ofac_sdn_entities) as total_entities,
    (SELECT COUNT(*) FROM ofac_alt_names) as total_alt_names,
    (SELECT COUNT(*) FROM sanctioned_addresses) as total_crypto_addresses,
    (SELECT COUNT(*) FROM sanctioned_addresses WHERE chain = 'ethereum') as ethereum_addresses,
    (SELECT COUNT(*) FROM sanctioned_addresses WHERE chain = 'bitcoin') as bitcoin_addresses,
    (SELECT MAX(updated_at) FROM ofac_sdn_entities) as last_update,
    (SELECT COUNT(*) FROM screening_results WHERE screened_at > NOW() - INTERVAL '24 hours') as screenings_24h,
    (SELECT COUNT(*) FROM screening_results WHERE is_match = TRUE AND screened_at > NOW() - INTERVAL '24 hours') as matches_24h;


-- Grant permissions (adjust as needed)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO forensics_app;
