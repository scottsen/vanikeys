-- VaniKeys Database Schema
-- PostgreSQL 14+
--
-- Core tables for VaniKeys gacha vanity key generation service.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Profile
    display_name VARCHAR(100),
    avatar_url TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    CONSTRAINT email_lowercase CHECK (email = LOWER(email))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at DESC);


-- Token balances table (one per user)
CREATE TABLE IF NOT EXISTS token_balances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Balance tracking
    balance INTEGER NOT NULL DEFAULT 0,
    lifetime_purchased INTEGER NOT NULL DEFAULT 0,
    lifetime_spent INTEGER NOT NULL DEFAULT 0,
    lifetime_usd_spent DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT positive_balance CHECK (balance >= 0),
    CONSTRAINT one_balance_per_user UNIQUE (user_id)
);

CREATE INDEX idx_token_balances_user_id ON token_balances(user_id);


-- Token transactions table (immutable audit log)
CREATE TABLE IF NOT EXISTS token_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Transaction details
    type VARCHAR(50) NOT NULL, -- 'purchase', 'spend', 'refund', 'admin', 'bonus'
    amount INTEGER NOT NULL,   -- Positive for credits, negative for debits
    description TEXT NOT NULL,

    -- Balance snapshot
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,

    -- Related records
    pull_id UUID,  -- If related to a pull
    purchase_id UUID,  -- If related to a purchase

    -- Timestamp (immutable)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    CONSTRAINT valid_transaction_type CHECK (type IN ('purchase', 'spend', 'refund', 'admin', 'bonus'))
);

CREATE INDEX idx_token_transactions_user_id ON token_transactions(user_id);
CREATE INDEX idx_token_transactions_created_at ON token_transactions(created_at DESC);
CREATE INDEX idx_token_transactions_pull_id ON token_transactions(pull_id) WHERE pull_id IS NOT NULL;
CREATE INDEX idx_token_transactions_purchase_id ON token_transactions(purchase_id) WHERE purchase_id IS NOT NULL;


-- Token purchases table (Stripe payments)
CREATE TABLE IF NOT EXISTS token_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Purchase details
    tokens INTEGER NOT NULL,
    bonus_tokens INTEGER NOT NULL DEFAULT 0,
    usd_amount DECIMAL(10, 2) NOT NULL,
    bundle_name VARCHAR(100),

    -- Payment provider (Stripe)
    stripe_payment_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'
    tokens_delivered BOOLEAN DEFAULT FALSE,
    transaction_id UUID, -- Link to token_transactions

    -- Error handling
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_purchase_status CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    CONSTRAINT positive_tokens CHECK (tokens > 0),
    CONSTRAINT positive_amount CHECK (usd_amount > 0)
);

CREATE INDEX idx_token_purchases_user_id ON token_purchases(user_id);
CREATE INDEX idx_token_purchases_status ON token_purchases(status);
CREATE INDEX idx_token_purchases_stripe_payment_id ON token_purchases(stripe_payment_id);
CREATE INDEX idx_token_purchases_created_at ON token_purchases(created_at DESC);


-- Patterns table (user-submitted patterns)
CREATE TABLE IF NOT EXISTS patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Pattern specification
    substrings TEXT[] NOT NULL,  -- Array of substrings
    mode VARCHAR(50) NOT NULL,   -- 'prefix', 'suffix', 'contains', 'multi', 'regex'
    fuzzy VARCHAR(50) NOT NULL DEFAULT 'none',  -- 'none', 'leetspeak', 'homoglyphs', 'phonetic'
    case_sensitive BOOLEAN DEFAULT FALSE,

    -- Computed properties (from ProbabilityCalculator)
    difficulty DOUBLE PRECISION,
    odds TEXT,  -- Human-readable: "1 in 4.2B"
    cost_tokens INTEGER,
    cost_guaranteed DECIMAL(10, 2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_mode CHECK (mode IN ('prefix', 'suffix', 'contains', 'multi', 'regex')),
    CONSTRAINT valid_fuzzy CHECK (fuzzy IN ('none', 'leetspeak', 'homoglyphs', 'phonetic')),
    CONSTRAINT non_empty_substrings CHECK (array_length(substrings, 1) > 0)
);

CREATE INDEX idx_patterns_user_id ON patterns(user_id);
CREATE INDEX idx_patterns_mode ON patterns(mode);
CREATE INDEX idx_patterns_created_at ON patterns(created_at DESC);


-- Pulls table (gacha pulls and guaranteed jobs)
CREATE TABLE IF NOT EXISTS pulls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pattern_id UUID NOT NULL REFERENCES patterns(id) ON DELETE RESTRICT,

    -- Pull type
    mode VARCHAR(50) NOT NULL,  -- 'gacha' or 'guaranteed'
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'success', 'failed', 'cancelled'

    -- Gacha mode
    cost_tokens INTEGER,
    rarity VARCHAR(50),  -- 'common', 'uncommon', 'rare', 'epic', 'legendary'

    -- Guaranteed mode
    cost_usd DECIMAL(10, 2),
    progress DOUBLE PRECISION DEFAULT 0.0,  -- 0.0 to 1.0
    estimated_completion TIMESTAMP WITH TIME ZONE,

    -- Result
    key_id UUID,  -- Primary generated key
    keys UUID[],  -- For multi-key results

    -- Performance metadata
    generation_time DOUBLE PRECISION DEFAULT 0.0,  -- Seconds
    attempts INTEGER DEFAULT 0,
    worker_id VARCHAR(255),

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_pull_mode CHECK (mode IN ('gacha', 'guaranteed')),
    CONSTRAINT valid_pull_status CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
    CONSTRAINT valid_rarity CHECK (rarity IS NULL OR rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')),
    CONSTRAINT valid_progress CHECK (progress >= 0.0 AND progress <= 1.0)
);

CREATE INDEX idx_pulls_user_id ON pulls(user_id);
CREATE INDEX idx_pulls_pattern_id ON pulls(pattern_id);
CREATE INDEX idx_pulls_status ON pulls(status);
CREATE INDEX idx_pulls_mode ON pulls(mode);
CREATE INDEX idx_pulls_created_at ON pulls(created_at DESC);
CREATE INDEX idx_pulls_running ON pulls(status) WHERE status IN ('pending', 'running');


-- Keys table (generated vanity keys)
CREATE TABLE IF NOT EXISTS keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pull_id UUID NOT NULL REFERENCES pulls(id) ON DELETE CASCADE,

    -- Key material
    did TEXT NOT NULL UNIQUE,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,  -- Encrypted in production!

    -- Match information
    matched_pattern TEXT NOT NULL,
    match_positions INTEGER[][],  -- Array of [start, end] pairs

    -- Generation metadata
    generation_time DOUBLE PRECISION DEFAULT 0.0,
    attempts INTEGER DEFAULT 0,
    worker_id VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT did_format CHECK (did LIKE 'did:key:z6Mk%')
);

CREATE INDEX idx_keys_pull_id ON keys(pull_id);
CREATE INDEX idx_keys_did ON keys(did);
CREATE INDEX idx_keys_created_at ON keys(created_at DESC);


-- Update timestamps trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_token_balances_updated_at BEFORE UPDATE ON token_balances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_token_purchases_updated_at BEFORE UPDATE ON token_purchases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pulls_updated_at BEFORE UPDATE ON pulls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- Views for common queries

-- User stats view
CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.id,
    u.username,
    u.email,
    u.created_at,
    COALESCE(tb.balance, 0) AS token_balance,
    COALESCE(tb.lifetime_purchased, 0) AS lifetime_tokens_purchased,
    COALESCE(tb.lifetime_spent, 0) AS lifetime_tokens_spent,
    COALESCE(tb.lifetime_usd_spent, 0) AS lifetime_usd_spent,
    COUNT(DISTINCT p.id) AS total_pulls,
    COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'success') AS successful_pulls,
    COUNT(DISTINCT k.id) AS total_keys
FROM users u
LEFT JOIN token_balances tb ON u.id = tb.user_id
LEFT JOIN pulls p ON u.id = p.user_id
LEFT JOIN keys k ON p.id = k.pull_id
GROUP BY u.id, u.username, u.email, u.created_at, tb.balance, tb.lifetime_purchased, tb.lifetime_spent, tb.lifetime_usd_spent;


-- Recent activity view
CREATE OR REPLACE VIEW recent_activity AS
SELECT
    'pull' AS activity_type,
    p.id AS activity_id,
    p.user_id,
    p.created_at,
    p.status,
    NULL::TEXT AS description
FROM pulls p
UNION ALL
SELECT
    'purchase' AS activity_type,
    tp.id AS activity_id,
    tp.user_id,
    tp.created_at,
    tp.status,
    tp.bundle_name AS description
FROM token_purchases tp
ORDER BY created_at DESC;


-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts';
COMMENT ON TABLE token_balances IS 'VaniToken balances (one per user)';
COMMENT ON TABLE token_transactions IS 'Immutable audit log of token movements';
COMMENT ON TABLE token_purchases IS 'Token purchase transactions via Stripe';
COMMENT ON TABLE patterns IS 'User-submitted vanity key patterns';
COMMENT ON TABLE pulls IS 'Gacha pulls and guaranteed generation jobs';
COMMENT ON TABLE keys IS 'Generated vanity keys';
