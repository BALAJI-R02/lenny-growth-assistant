-- Lenny Growth Assistant — Database Initialization
-- This runs once on first postgres start via docker-entrypoint-initdb.d/

-- Enable needed extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_meta   JSONB NOT NULL DEFAULT '{}'
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    citations   JSONB NOT NULL DEFAULT '[]',
    route       TEXT,
    provider    TEXT,
    model       TEXT,
    latency_ms  INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_session_id_idx ON messages(session_id);
CREATE INDEX IF NOT EXISTS messages_created_at_idx ON messages(created_at);

-- Chunks table (transcript segments)
CREATE TABLE IF NOT EXISTS chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode     TEXT NOT NULL,
    guest       TEXT NOT NULL DEFAULT '',
    source_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text        TEXT NOT NULL,
    tsv         TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    UNIQUE(source_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING GIN(tsv);
CREATE INDEX IF NOT EXISTS chunks_episode_idx ON chunks(episode);

-- Artifacts table
CREATE TABLE IF NOT EXISTS artifacts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('markdown', 'html')),
    title       TEXT NOT NULL DEFAULT 'Untitled',
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS artifacts_session_id_idx ON artifacts(session_id);
