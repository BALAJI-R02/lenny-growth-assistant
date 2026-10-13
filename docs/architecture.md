# Architecture — The Lenny Growth Assistant

**Version:** 1.0 | **Date:** 2026-10-12

---

## 1. High-Level Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Network                       │
│                                                                      │
│  ┌──────────────┐   HTTP/REST    ┌──────────────────────────────┐  │
│  │   React/Vite │ ◄────────────► │   FastAPI Backend             │  │
│  │   Frontend   │                │   (Python 3.12)               │  │
│  │  :3000       │                │   :8000                       │  │
│  └──────────────┘                │   /api/v1/*                   │  │
│                                  └──────────┬───────────────────┘  │
│                                             │                       │
│                                  ┌──────────▼───────────────────┐  │
│                                  │   PostgreSQL 16               │  │
│                                  │   sessions / messages /       │  │
│                                  │   chunks / artifacts          │  │
│                                  │   :5432                       │  │
│                                  └──────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
         │ host.docker.internal:11434
         ▼
   Ollama (host)          Anthropic / OpenAI (internet)
```

---

## 2. Database Schema

```sql
-- Sessions: one per conversation
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ DEFAULT now(),
    user_meta   JSONB DEFAULT '{}'
);

-- Messages: persisted chat turns
CREATE TABLE messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
    content     TEXT NOT NULL,
    citations   JSONB DEFAULT '[]',
    route       TEXT,                  -- QA | ESSAY | ARTIFACT
    provider    TEXT,
    model       TEXT,
    latency_ms  INTEGER,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Chunks: ingested transcript segments
CREATE TABLE chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode     TEXT NOT NULL,
    guest       TEXT NOT NULL DEFAULT '',
    source_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text        TEXT NOT NULL,
    tsv         TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    UNIQUE(source_path, chunk_index)
);
CREATE INDEX chunks_tsv_gin ON chunks USING GIN(tsv);

-- Artifacts: generated docs/HTML
CREATE TABLE artifacts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID REFERENCES sessions(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('markdown','html')),
    title       TEXT NOT NULL DEFAULT 'Untitled',
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

---

## 3. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | DB, LLM provider, index status |
| GET | `/debug/status` | Detailed diagnostics |
| POST | `/api/v1/sessions` | Create session, returns `{session_id}` |
| GET | `/api/v1/sessions/{id}/messages` | Load conversation history |
| POST | `/api/v1/sessions/{id}/chat` | Send message, get routed response |
| GET | `/api/v1/artifacts/{id}` | Fetch artifact |
| GET | `/api/v1/artifacts/{id}/raw` | Raw content for download |
| POST | `/api/v1/ingest/trigger` | Manually trigger ingest (dev only) |

### Chat Request/Response
```json
// POST /api/v1/sessions/{id}/chat
{ "content": "What does Lenny say about retention?" }

// Response
{
  "id": "uuid",
  "role": "assistant",
  "content": "According to [1]...",
  "route": "QA",
  "citations": [
    {"ref": 1, "episode": "ep-123", "guest": "Brian Balfour",
     "source_path": "transcripts/ep-123.md", "snippet": "..."}
  ],
  "provider": "ollama",
  "model": "llama3.2",
  "latency_ms": 4200,
  "artifact_id": null
}
```

### Error Contract
```json
{
  "error": {
    "code": "LLM_UNAVAILABLE",
    "message": "Ollama is unreachable and no cloud fallback key is configured.",
    "request_id": "uuid"
  }
}
```

---

## 4. Component Architecture

### Backend (`backend/app/`)
```
app/
├── main.py              # FastAPI app factory, middleware, CORS
├── config.py            # Settings (Pydantic v2 BaseSettings)
├── database.py          # Async SQLAlchemy engine + session
├── models/
│   ├── db.py            # SQLAlchemy ORM models
│   └── schemas.py       # Pydantic request/response schemas
├── routers/
│   ├── health.py        # /health, /debug/status
│   ├── sessions.py      # session CRUD
│   └── chat.py          # main chat endpoint
├── services/
│   ├── router.py        # Message classifier (keyword + LLM fallback)
│   ├── retrieval.py     # Postgres FTS service
│   ├── llm.py           # Provider abstraction layer
│   ├── qa.py            # QA pipeline
│   ├── essay.py         # Essay pipeline (Ship30 skill)
│   ├── artifact.py      # Artifact generation + sanitization
│   └── query_rewriter.py # Follow-up -> standalone query
└── skills/
    └── ship30/
        └── SKILL.md     # Ship 30 for 30 writing principles
```

### Frontend (`frontend/src/`)
```
src/
├── components/
│   ├── ChatPanel.tsx        # Left: message list + input
│   ├── ArtifactViewer.tsx   # Right: payload viewer
│   ├── MessageBubble.tsx    # Single chat turn
│   ├── CitationChip.tsx     # [EP // Guest] expandable chip
│   ├── RetrievalTrace.tsx   # Chunk + score panel
│   ├── StatusBar.tsx        # DB/MODEL/INDEX/SANDBOX indicators
│   ├── BootSequence.tsx     # Skippable SOC boot animation
│   └── ProviderBadge.tsx    # UPLINK LOCAL/CLOUD indicator
├── hooks/
│   ├── useSession.ts        # Session create/load
│   └── useChat.ts           # Message send + optimistic update
├── store/
│   └── chatStore.ts         # Zustand global state
├── types/
│   └── index.ts             # Shared TypeScript types
└── utils/
    ├── sanitize.ts          # Client-side DOMPurify wrapper
    └── artifact.ts          # Iframe srcdoc builder + CSP injector
```

---

## 5. Ingestion Pipeline

```
GitHub (ChatPRD/lennys-podcast-transcripts)
  -> git clone / sparse checkout to /tmp/transcripts
  -> Walk .md files
  -> Extract: episode (from filename), guest (from YAML frontmatter or filename)
  -> Chunk by ~500 tokens with 50-token overlap (sentence boundary preferred)
  -> Upsert into chunks table (idempotent: ON CONFLICT(source_path, chunk_index) DO UPDATE)
  -> Rebuild GIN index (happens automatically on upsert)
  -> Log: file count, chunk count, duration
```

**Capping strategy:** Ingest first 60 episodes alphabetically if total chunks > 50,000. Document in logs.

---

## 6. Retrieval

```sql
SELECT id, episode, guest, source_path, text,
       ts_rank(tsv, query) AS score
FROM chunks, to_tsquery('english', :q) query
WHERE tsv @@ query
ORDER BY score DESC
LIMIT 8;
```

- **top_k:** 8 chunks default (configurable via `RETRIEVAL_TOP_K` env)
- **Empty threshold:** If no rows returned → "NO INTEL FOUND" path
- **Weak threshold:** If max score < 0.1 → treat as empty (configurable)
- **Future:** pgvector embedding search with cosine similarity; hybrid reranking

---

## 7. Routing Logic

```python
# Keyword rules (fast path)
ESSAY_KEYWORDS = ["write an essay", "ship 30 essay", "draft an essay", "write a ship30"]
ARTIFACT_KEYWORDS = ["generate artifact", "create html", "create markdown",
                     "generate doc", "make a document", "write html"]
# Everything else -> QA (LLM fallback classifier only when ambiguous)

def classify(message: str) -> Route:
    lower = message.lower()
    if any(k in lower for k in ESSAY_KEYWORDS): return Route.ESSAY
    if any(k in lower for k in ARTIFACT_KEYWORDS): return Route.ARTIFACT
    return Route.QA  # default
```

LLM fallback: if `ROUTER_USE_LLM=true` and message is ambiguous (contains both artifact+essay signals), ask LLM to choose.

---

## 8. LLM Provider Abstraction

```python
# config: LLM_PROVIDER = "ollama" | "anthropic" | "openai"
class LLMProvider(Protocol):
    async def complete(self, messages: list[dict], **kwargs) -> str: ...

# Selection order:
# 1. Try LLM_PROVIDER
# 2. If Ollama unreachable + ANTHROPIC_API_KEY set -> fallback to anthropic
# 3. If Ollama unreachable + OPENAI_API_KEY set -> fallback to openai
# 4. Otherwise -> raise LLMUnavailableError
```

**Justification for NOT using Claude Agent SDK / Pi Coding Agent:**
The spec allows "choose whichever works with Ollama fastest." A direct HTTP provider abstraction adds zero overhead vs. an agent framework, works with Ollama out of the box, and avoids SDK dependency conflicts. Agent SDK is appropriate when tool-use loops are needed; our routes are single-pass.

---

## 9. Artifact Security

### HTML Pipeline
```
LLM output (HTML string)
  -> bleach.clean(strip=True, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
  -> Remove any remaining: <script>, on* attrs, javascript: hrefs, external src/href
  -> Inject CSP meta: <meta http-equiv="Content-Security-Policy"
       content="default-src 'none'; style-src 'unsafe-inline'; img-src data:;">
  -> Wrap in <iframe sandbox="allow-same-origin" srcdoc="...">
     (no allow-scripts, no allow-popups, no allow-forms)
```

### Markdown Pipeline
```
LLM output (Markdown string)
  -> react-markdown with remarkGfm
  -> rehype-sanitize (default schema, no raw HTML)
  -> All links get rel="noopener noreferrer" target="_blank"
  -> DOMPurify.sanitize() as final client-side pass
```

---

## 10. Observability

Structured JSON log per request:
```json
{
  "timestamp": "2026-10-12T11:00:00Z",
  "request_id": "uuid",
  "session_id": "uuid",
  "route": "QA",
  "provider": "ollama",
  "model": "llama3.2",
  "retrieval_hit_count": 5,
  "retrieval_max_score": 0.45,
  "latency_ms": 3200,
  "error_type": null
}
```

---

## 11. Deployment Topology

```
Host machine:
  - Docker Desktop
  - Ollama daemon (port 11434)
  - git, make

Docker Compose services:
  - postgres:16 (port 5432, volume: pgdata)
  - backend (port 8000, depends_on postgres)
  - frontend (port 3000, depends_on backend)

Network: lenny_net (bridge)
Backend reaches Ollama via host.docker.internal:11434
```

---

## 12. Future Work

1. **pgvector:** Add `vector(1536)` column to chunks; hybrid BM25+cosine reranking
2. **Streaming:** SSE endpoint for token streaming with aria-live
3. **Auth:** JWT + row-level security in Postgres
4. **Eval pipeline:** Automated RAGAS evaluation of citation quality
5. **Episode metadata API:** Fetch episode list from Lenny's RSS feed for richer citations
