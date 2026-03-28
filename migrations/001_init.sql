CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    plan        VARCHAR(50)  NOT NULL DEFAULT 'starter',
    credits     INTEGER      NOT NULL DEFAULT 1000,
    is_active   BOOLEAN      NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE audit_log (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenants(id),
    model          VARCHAR(100) NOT NULL,
    input_tokens   INTEGER,
    output_tokens  INTEGER,
    cost_usd       NUMERIC(10,6),
    latency_ms     INTEGER,
    cached         BOOLEAN DEFAULT false,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_tenant ON audit_log(tenant_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

CREATE TABLE semantic_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    query_embedding vector(384),
    query_text      TEXT NOT NULL,
    response_text   TEXT NOT NULL,
    model           VARCHAR(100),
    hit_count       INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_cache_tenant ON semantic_cache(tenant_id);
CREATE INDEX idx_cache_embedding ON semantic_cache
    USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 100);