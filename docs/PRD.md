# PRD — The Lenny Growth Assistant

**Version:** 1.0  
**Date:** 2026-10-12  
**Author:** AI Engineering (take-home assessment)  
**Status:** Approved for build

---

## 1. Discovery Brief

### 1.1 User
A **Forward Deployed Engineer / PM candidate** (or product practitioner) who wants to:
- Ask product/growth questions and get answers grounded in real Lenny's Podcast transcript evidence.
- Generate a publication-ready ~1,250-word Ship 30 for 30 essay on a growth topic, with citations.
- Produce Markdown documentation or self-contained HTML artifacts from the conversation.

### 1.2 Problem
Lenny Rachitsky's podcast contains hundreds of high-signal product/growth conversations, but surfacing specific actionable insights requires listening to full episodes. Practitioners waste hours seeking evidence they already know exists somewhere in the canon.

### 1.3 Success Metrics
| Metric | Target |
|---|---|
| QA answers with valid citation | >= 90% |
| Essay word count accuracy | 1,150-1,350 words |
| Artifact sanitization tests pass | 100% |
| p95 QA response latency (Ollama) | < 15 s |
| Empty retrieval "NO INTEL FOUND" rate on off-topic | >= 95% |

---

## 2. Assumptions

| # | Assumption |
|---|---|
| A1 | `ChatPRD/lennys-podcast-transcripts` on GitHub is the canonical public transcript repo |
| A2 | Ollama runs on Docker host, reachable at `host.docker.internal:11434` |
| A3 | Default model `llama3.2` is sufficient for routing + QA |
| A4 | Full-text search (tsvector + ts_rank) is sufficient for MVP; pgvector deferred |
| A5 | Session UUID is sufficient auth for MVP (no login) |

---

## 3. Scope

### In Scope (v1)
- Chat interface with session management
- Three routes: QA (with citations), ESSAY, ARTIFACT
- Postgres full-text retrieval from Lenny transcript corpus
- Provider abstraction: Ollama (default), Anthropic, OpenAI
- Automatic fallback: Ollama -> cloud if unreachable + key exists
- Artifact viewer with sandboxed HTML iframe + Markdown rendering
- Security: server-side HTML sanitization + CSP + DOMPurify
- SOC Console dark UI theme with real-time status indicators
- pytest suite (LLM mocked, runs offline)
- Docker Compose deployment

### Out of Scope (v1)
- User authentication / multi-tenancy
- Embedding-based retrieval (pgvector - future work)
- Streaming token-by-token responses
- Rate limiting / usage billing

---

## 4. User Flows

### 4.1 QA Flow
```
User types question
  -> Router classifies as QA
  -> Query rewriter (if follow-up)
  -> Postgres FTS retrieves top-k chunks
  -> If empty/weak -> return "NO INTEL FOUND"
  -> LLM answers ONLY from chunks -> cites [1],[2]
  -> EVIDENCE chips shown below message
  -> Retrieval trace panel shows chunks + scores
```

### 4.2 Essay Flow
```
User requests essay on topic X
  -> Router classifies as ESSAY
  -> skills/ship30/SKILL.md principles loaded
  -> Retrieve top-k relevant chunks
  -> LLM drafts ~1,250-word essay with Ship30 structure
  -> Word count check -> retry once if out of range
  -> Essay stored as artifact, sent to PAYLOAD VIEWER
```

### 4.3 Artifact Flow
```
User requests doc/HTML artifact
  -> Router classifies as ARTIFACT
  -> LLM generates Markdown or HTML
  -> Server sanitizes HTML
  -> Stored in artifacts table
  -> Sent to PAYLOAD VIEWER with Preview/Source/Copy/Download
  -> "CONTAINMENT: ACTIVE" badge shown
```

---

## 5. Acceptance Criteria

- AC-1: QA cites at least one [EP // Guest] chip per answer; off-topic -> "NO INTEL FOUND"
- AC-2: Follow-up rewrites to standalone query; sessions are isolated
- AC-3: Essay is 1,150-1,350 words with Ship30 structure and citations
- AC-4: Malicious HTML payloads stripped; CONTAINMENT badge present
- AC-5: Provider switch via .env works; clear error when both unavailable
- AC-6: /health reflects real component state; logs contain required fields
- AC-7: `make test` passes offline

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| Hallucination | Answer-only-from-chunks prompt; strict "NO INTEL FOUND" |
| High latency (local Ollama) | Stream responses; p95 budget 15s |
| Unsafe artifact rendering | Sandbox iframe; CSP; DOMPurify; strip server-side |
| Cross-session data leakage | session_id isolation; parameterized queries |
| Transcript repo unavailable | Ingest is idempotent; cap at 50 episodes if slow |
