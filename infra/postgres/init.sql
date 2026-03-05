-- AI Studio OS — PostgreSQL init
-- Run once on first startup via Docker entrypoint

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── OPPORTUNITIES ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS opportunities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    description     TEXT,
    category        TEXT,           -- 'open_call' | 'residency' | 'commission' | 'festival'
    organizer       TEXT,
    location        TEXT,
    country         TEXT,
    deadline        DATE,
    fee             TEXT,
    award           TEXT,
    url             TEXT UNIQUE,
    tags            TEXT[],
    is_active       BOOLEAN DEFAULT TRUE,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_opportunities_embedding
    ON opportunities USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_opportunities_deadline ON opportunities (deadline);
CREATE INDEX IF NOT EXISTS idx_opportunities_category ON opportunities (category);

-- ─── ARCHITECTURE LOCATIONS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS architecture_locations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    description     TEXT,
    architect       TEXT,
    city            TEXT,
    country         TEXT,
    coordinates     POINT,          -- lat/lng
    style           TEXT,           -- brutalist, modernist, etc.
    year_built      INT,
    suitability     TEXT[],         -- ['photography', 'installation', 'performance']
    image_urls      TEXT[],
    source_url      TEXT,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_arch_embedding
    ON architecture_locations USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ─── COLLECTORS ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS collectors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    bio             TEXT,
    location        TEXT,
    country         TEXT,
    interests       TEXT[],         -- artistic interests / genres
    known_works     TEXT[],         -- notable collected works
    institutions    TEXT[],         -- affiliated galleries/museums
    contact_email   TEXT,
    contact_url     TEXT,
    social_links    JSONB,
    notes           TEXT,           -- private studio notes
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collectors_embedding
    ON collectors USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_collectors_name ON collectors USING gin (to_tsvector('english', name));

-- ─── CURATORS ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS curators (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    bio             TEXT,
    institution     TEXT,
    role            TEXT,
    location        TEXT,
    country         TEXT,
    focus_areas     TEXT[],
    notable_shows   TEXT[],
    contact_email   TEXT,
    contact_url     TEXT,
    social_links    JSONB,
    notes           TEXT,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curators_embedding
    ON curators USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ─── PRESS ITEMS ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS press_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    content         TEXT,
    summary         TEXT,
    source          TEXT,           -- publication name
    author          TEXT,
    url             TEXT UNIQUE,
    published_at    TIMESTAMPTZ,
    category        TEXT,           -- 'exhibition' | 'review' | 'news' | 'interview'
    tags            TEXT[],
    mentioned_artists TEXT[],
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_press_embedding
    ON press_items USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_press_published ON press_items (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_press_fts
    ON press_items USING gin (to_tsvector('english', title || ' ' || COALESCE(content, '')));

-- ─── PROPOSALS ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS proposals (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title               TEXT NOT NULL,
    opportunity_id      UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    content             TEXT NOT NULL,
    status              TEXT DEFAULT 'draft',  -- 'draft' | 'submitted' | 'accepted' | 'rejected'
    submitted_at        TIMESTAMPTZ,
    response_at         TIMESTAMPTZ,
    notes               TEXT,
    embedding           vector(1536),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_proposals_embedding
    ON proposals USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals (status);

-- ─── KNOWLEDGE ITEMS ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    summary         TEXT,
    source_type     TEXT NOT NULL,  -- 'note' | 'article' | 'pdf' | 'url' | 'reference'
    source_url      TEXT,
    author          TEXT,
    tags            TEXT[],
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
    ON knowledge_items USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_knowledge_fts
    ON knowledge_items USING gin (to_tsvector('english', title || ' ' || content));
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_items USING gin (tags);

-- ─── AUTO-UPDATE updated_at ──────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'opportunities', 'architecture_locations', 'collectors',
        'curators', 'press_items', 'proposals', 'knowledge_items'
    ] LOOP
        EXECUTE format('
            CREATE TRIGGER set_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at()
        ', t);
    END LOOP;
END $$;
