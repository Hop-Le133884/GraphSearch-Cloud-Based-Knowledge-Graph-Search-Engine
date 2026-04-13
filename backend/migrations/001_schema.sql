-- ===========================
-- USERS
-- ===========================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    pass_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT now()
);

-- ===========================
-- QUERY LOGS
-- Every search request is recorded here,
-- user_id is nullable -- anonymous users can search too.
-- ===========================
CREATE TABLE IF NOT EXISTS query_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    cypher_query TEXT,
    latency_ms INTEGER NOT NULL,
    result_count INTEGER,
    cache_hit BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now()
);

-- ==========================
-- RESULT CACHE
-- One cached result per unique query (keyed by hash),
-- ==========================
CREATE TABLE IF NOT EXISTS result_cache (
    query_hash VARCHAR(64) PRIMARY KEY,
    query_text TEXT NOT NULL,
    result_json JSONB NOT NULL,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    expires_at TIMESTAMP DEFAULT now() + INTERVAL '24 hours'
);