-- AppSumo Code Management System
-- Unterstützt Multi-Product-Management

CREATE TABLE IF NOT EXISTS appsumo_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    product VARCHAR(100) NOT NULL, -- 'chatbot', 'wallet-guardian', 'transaction-inspector', 'analytics'
    tier INTEGER NOT NULL, -- 1, 2, or 3
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'redeemed', 'expired', 'deactivated'
    
    -- Redemption
    redeemed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    redeemed_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    created_by_admin_id UUID REFERENCES users(id),
    
    -- AppSumo Integration
    appsumo_invoice_id VARCHAR(100),
    appsumo_purchase_date TIMESTAMP,
    
    -- Analytics
    redemption_ip INET,
    redemption_user_agent TEXT,
    
    -- Constraints
    CHECK (tier IN (1, 2, 3)),
    CHECK (status IN ('active', 'redeemed', 'expired', 'deactivated'))
);

-- Index für schnelle Lookups
CREATE INDEX idx_appsumo_codes_code ON appsumo_codes(code);
CREATE INDEX idx_appsumo_codes_status ON appsumo_codes(status);
CREATE INDEX idx_appsumo_codes_product ON appsumo_codes(product);
CREATE INDEX idx_appsumo_codes_redeemed_by ON appsumo_codes(redeemed_by_user_id);

-- User-Product-Activations (was User hat aktiviert)
CREATE TABLE IF NOT EXISTS appsumo_activations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_id UUID NOT NULL REFERENCES appsumo_codes(id) ON DELETE CASCADE,
    product VARCHAR(100) NOT NULL,
    tier INTEGER NOT NULL,
    
    -- Activation Details
    activated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- NULL = lifetime
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'expired', 'cancelled'
    
    -- Features granted
    features JSONB DEFAULT '{}',
    limits JSONB DEFAULT '{}',
    
    -- Analytics
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    UNIQUE(user_id, product),
    CHECK (tier IN (1, 2, 3)),
    CHECK (status IN ('active', 'expired', 'cancelled'))
);

CREATE INDEX idx_appsumo_activations_user ON appsumo_activations(user_id);
CREATE INDEX idx_appsumo_activations_product ON appsumo_activations(product);
CREATE INDEX idx_appsumo_activations_status ON appsumo_activations(status);

-- Revenue Tracking
CREATE TABLE IF NOT EXISTS appsumo_revenue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_id UUID NOT NULL REFERENCES appsumo_codes(id),
    product VARCHAR(100) NOT NULL,
    tier INTEGER NOT NULL,
    
    -- Revenue
    amount_usd DECIMAL(10, 2) NOT NULL,
    appsumo_fee_usd DECIMAL(10, 2), -- 70% cut
    net_revenue_usd DECIMAL(10, 2),
    
    -- Dates
    sale_date TIMESTAMP NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),
    
    -- Conversion Tracking
    converted_to_saas BOOLEAN DEFAULT FALSE,
    conversion_date TIMESTAMP,
    monthly_recurring_revenue DECIMAL(10, 2)
);

CREATE INDEX idx_appsumo_revenue_product ON appsumo_revenue(product);
CREATE INDEX idx_appsumo_revenue_sale_date ON appsumo_revenue(sale_date);

COMMENT ON TABLE appsumo_codes IS 'AppSumo redemption codes for all products';
COMMENT ON TABLE appsumo_activations IS 'User product activations from AppSumo codes';
COMMENT ON TABLE appsumo_revenue IS 'Revenue tracking for AppSumo sales';
