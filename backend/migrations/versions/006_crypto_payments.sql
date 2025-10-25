-- Phase 6: Crypto Payment Tables
-- NOWPayments integration for cryptocurrency subscription payments

-- Payment Status Enum
CREATE TYPE payment_status AS ENUM (
    'pending',
    'waiting',
    'confirming',
    'confirmed',
    'sending',
    'finished',
    'failed',
    'expired',
    'refunded'
);

-- Crypto Payments Table
CREATE TABLE IF NOT EXISTS crypto_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- NOWPayments IDs
    payment_id BIGINT UNIQUE NOT NULL,  -- NOWPayments payment ID
    order_id VARCHAR(255) UNIQUE NOT NULL,  -- Our internal order ID
    
    -- User & Subscription
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(50) NOT NULL,  -- community, starter, pro, business, plus, enterprise
    
    -- Payment Details
    price_amount DECIMAL(18, 2) NOT NULL,  -- Amount in USD
    price_currency VARCHAR(10) DEFAULT 'usd',
    pay_amount DECIMAL(36, 18) NOT NULL,  -- Amount in crypto (high precision)
    pay_currency VARCHAR(10) NOT NULL,  -- btc, eth, usdt, etc.
    
    -- Transaction Info
    pay_address VARCHAR(255),  -- Deposit address
    payin_extra_id VARCHAR(255),  -- Extra ID for some currencies (XRP, XLM)
    pay_in_hash VARCHAR(255),  -- Blockchain transaction hash
    
    -- Status
    payment_status payment_status DEFAULT 'pending' NOT NULL,
    
    -- Exchange Rate
    actual_pay_amount DECIMAL(36, 18),  -- Actual amount received
    outcome_amount DECIMAL(18, 2),  -- Amount we receive after fees
    outcome_currency VARCHAR(10) DEFAULT 'usd',
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Payment expiration
    
    -- Purchase Info
    purchase_id VARCHAR(255),  -- NOWPayments purchase_id
    invoice_url VARCHAR(512),  -- Payment page URL
    
    -- Webhooks
    last_webhook_at TIMESTAMP,
    webhook_count INTEGER DEFAULT 0,
    
    -- Notes
    notes TEXT  -- Admin notes or error messages
);

-- Indexes for crypto_payments
CREATE INDEX idx_crypto_payments_payment_id ON crypto_payments(payment_id);
CREATE INDEX idx_crypto_payments_order_id ON crypto_payments(order_id);
CREATE INDEX idx_crypto_payments_user ON crypto_payments(user_id);
CREATE INDEX idx_crypto_payments_status ON crypto_payments(payment_status);
CREATE INDEX idx_crypto_payments_hash ON crypto_payments(pay_in_hash);
CREATE INDEX idx_crypto_payments_created ON crypto_payments(created_at DESC);
CREATE INDEX idx_crypto_payments_plan ON crypto_payments(plan_name);
CREATE INDEX idx_crypto_payments_currency ON crypto_payments(pay_currency);

-- Crypto Subscriptions Table
CREATE TABLE IF NOT EXISTS crypto_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- User & Plan
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(50) NOT NULL,
    
    -- Payment Details
    currency VARCHAR(10) NOT NULL,  -- btc, eth, etc.
    amount_usd DECIMAL(18, 2) NOT NULL,
    
    -- Billing
    interval VARCHAR(20) NOT NULL,  -- monthly, yearly
    next_billing_date TIMESTAMP NOT NULL,
    last_payment_date TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    cancelled_at TIMESTAMP,
    
    -- Payment History
    successful_payments INTEGER DEFAULT 0,
    failed_payments INTEGER DEFAULT 0
);

-- Indexes for crypto_subscriptions
CREATE INDEX idx_crypto_subscriptions_user ON crypto_subscriptions(user_id);
CREATE INDEX idx_crypto_subscriptions_active ON crypto_subscriptions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_crypto_subscriptions_next_billing ON crypto_subscriptions(next_billing_date);
CREATE INDEX idx_crypto_subscriptions_plan ON crypto_subscriptions(plan_name);

-- Trigger to update updated_at on crypto_payments
CREATE OR REPLACE FUNCTION update_crypto_payments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER crypto_payments_updated_at
BEFORE UPDATE ON crypto_payments
FOR EACH ROW
EXECUTE FUNCTION update_crypto_payments_updated_at();

-- Trigger to update updated_at on crypto_subscriptions
CREATE OR REPLACE FUNCTION update_crypto_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER crypto_subscriptions_updated_at
BEFORE UPDATE ON crypto_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_crypto_subscriptions_updated_at();

-- Comments
COMMENT ON TABLE crypto_payments IS 'Cryptocurrency payment tracking via NOWPayments';
COMMENT ON TABLE crypto_subscriptions IS 'Recurring crypto subscriptions for billing automation';
COMMENT ON COLUMN crypto_payments.payment_id IS 'NOWPayments payment ID (external)';
COMMENT ON COLUMN crypto_payments.order_id IS 'Internal order ID (UUID format)';
COMMENT ON COLUMN crypto_payments.pay_amount IS 'Crypto amount with high precision for all currencies';
COMMENT ON COLUMN crypto_payments.pay_in_hash IS 'Blockchain transaction hash for verification';
COMMENT ON COLUMN crypto_subscriptions.interval IS 'Billing interval: monthly or yearly';
COMMENT ON COLUMN crypto_subscriptions.next_billing_date IS 'Next scheduled billing date for automation';
