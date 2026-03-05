-- AI Studio OS — Migration V2: Additional Tables & Fields
-- Safe to run multiple times (uses IF NOT EXISTS)

-- ═══════════════════════════════════════════════════════════════════════════
-- NEW TABLES
-- ═══════════════════════════════════════════════════════════════════════════

-- Artists table
CREATE TABLE IF NOT EXISTS artists (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    country         TEXT,
    city            TEXT,
    bio             TEXT,
    medium          TEXT[],
    website         TEXT,
    instagram       TEXT,
    represented_by  TEXT[],
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Artworks table
CREATE TABLE IF NOT EXISTS artworks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    artist_id       UUID REFERENCES artists(id) ON DELETE SET NULL,
    year            INTEGER,
    medium          TEXT,
    dimensions      TEXT,
    description     TEXT,
    image_urls      TEXT[],
    collection      TEXT,
    exhibition_history TEXT[],
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Institutions table (separate from curators)
CREATE TABLE IF NOT EXISTS institutions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    city            TEXT,
    country         TEXT,
    type            TEXT,
    website         TEXT,
    focus_areas     TEXT[],
    annual_budget   TEXT,
    digital_art_program BOOLEAN DEFAULT FALSE,
    notes           TEXT,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Exhibitions table
CREATE TABLE IF NOT EXISTS exhibitions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    institution_id  UUID REFERENCES institutions(id) ON DELETE SET NULL,
    curator_id      UUID,
    start_date      DATE,
    end_date        DATE,
    type            TEXT,
    artists         TEXT[],
    description     TEXT,
    url             TEXT,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════════
-- RELATIONSHIP TABLES (Many-to-Many)
-- ═══════════════════════════════════════════════════════════════════════════

-- Collector <-> Artist relationships
CREATE TABLE IF NOT EXISTS collector_artist_relations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collector_id    UUID REFERENCES collectors(id) ON DELETE CASCADE,
    artist_id       UUID REFERENCES artists(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'collects',
    confidence      FLOAT DEFAULT 0.5,
    source          TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(collector_id, artist_id)
);

-- Artist <-> Institution relationships
CREATE TABLE IF NOT EXISTS artist_institution_relations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artist_id       UUID REFERENCES artists(id) ON DELETE CASCADE,
    institution_id  UUID REFERENCES institutions(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'exhibited',
    year            INTEGER,
    exhibition_title TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Artist <-> Gallery relationships
CREATE TABLE IF NOT EXISTS artist_gallery_relations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artist_id       UUID REFERENCES artists(id) ON DELETE CASCADE,
    gallery_name    TEXT NOT NULL,
    relationship_type TEXT DEFAULT 'represented',
    start_year      INTEGER,
    end_year        INTEGER,
    is_current      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════════
-- ADD MISSING COLUMNS TO EXISTING TABLES (safe - uses IF NOT EXISTS pattern)
-- ═══════════════════════════════════════════════════════════════════════════

-- Enhanced architecture_locations fields
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='architecture_locations' AND column_name='photography_score') THEN
        ALTER TABLE architecture_locations ADD COLUMN photography_score INTEGER CHECK (photography_score >= 1 AND photography_score <= 10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='architecture_locations' AND column_name='access_risk') THEN
        ALTER TABLE architecture_locations ADD COLUMN access_risk TEXT CHECK (access_risk IN ('low', 'medium', 'high', 'restricted'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='architecture_locations' AND column_name='historical_significance') THEN
        ALTER TABLE architecture_locations ADD COLUMN historical_significance TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='architecture_locations' AND column_name='architecture_uniqueness') THEN
        ALTER TABLE architecture_locations ADD COLUMN architecture_uniqueness INTEGER CHECK (architecture_uniqueness >= 1 AND architecture_uniqueness <= 10);
    END IF;
END $$;

-- Enhanced opportunities fields
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='fit_score') THEN
        ALTER TABLE opportunities ADD COLUMN fit_score FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='digital_art_relevance') THEN
        ALTER TABLE opportunities ADD COLUMN digital_art_relevance INTEGER CHECK (digital_art_relevance >= 1 AND digital_art_relevance <= 10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='installation_scale') THEN
        ALTER TABLE opportunities ADD COLUMN installation_scale TEXT CHECK (installation_scale IN ('small', 'medium', 'large', 'monumental'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='architecture_relevance') THEN
        ALTER TABLE opportunities ADD COLUMN architecture_relevance INTEGER CHECK (architecture_relevance >= 1 AND architecture_relevance <= 10);
    END IF;
END $$;

-- Enhanced collectors fields
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='collectors' AND column_name='price_range') THEN
        ALTER TABLE collectors ADD COLUMN price_range TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='collectors' AND column_name='museum_boards') THEN
        ALTER TABLE collectors ADD COLUMN museum_boards TEXT[];
    END IF;
END $$;

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES FOR NEW TABLES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_artists_embedding ON artists USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_artworks_embedding ON artworks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_institutions_embedding ON institutions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_exhibitions_embedding ON exhibitions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_artworks_artist ON artworks(artist_id);
CREATE INDEX IF NOT EXISTS idx_exhibitions_institution ON exhibitions(institution_id);
CREATE INDEX IF NOT EXISTS idx_collector_artist_collector ON collector_artist_relations(collector_id);
CREATE INDEX IF NOT EXISTS idx_collector_artist_artist ON collector_artist_relations(artist_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- UPDATED_AT TRIGGERS FOR NEW TABLES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TRIGGER set_updated_at_artists
    BEFORE UPDATE ON artists
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_updated_at_artworks
    BEFORE UPDATE ON artworks
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_updated_at_institutions
    BEFORE UPDATE ON institutions
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_updated_at_exhibitions
    BEFORE UPDATE ON exhibitions
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
