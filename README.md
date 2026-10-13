# 🎙️ The Lenny Growth Assistant

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=flat-square&logo=ollama&logoColor=white)](https://ollama.com)
[![Docker](https://img.shields.io/badge/Docker-Compose_v2-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**AI-powered product & growth intelligence grounded in hundreds of Lenny Rachitsky's podcast interviews.**  
*Ask strategic product questions with verified transcript citations, generate publication-grade Ship 30 for 30 essays, and preview interactive sandboxed artifacts in a real-time command console.*

[Features](#-key-features) • [Architecture](#-architecture) • [Quickstart](#-quickstart) • [Routing Engine](#-query-routing-engine) • [Security & Containment](#-security--artifact-containment) • [API Specs](#-api-endpoints)

</div>

---

## ⚡ Key Features

- 🔎 **Zero-Hallucination Retrieval:** Answers exclusively cite actual podcast statements. If the evidence isn't in the corpus, it outputs a strict `"NO INTEL FOUND"` notice.
- 🏷️ **Interactive Evidence Chips:** Inspect the exact episode number, guest name, timestamp snippet, and PostgreSQL `ts_rank` relevance score.
- ✍️ **Ship 30 for 30 Essay Generator:** Automatically structures ~1,250-word atomic essays with hooks, frameworks, and guest quotes.
- 🛡️ **Multi-Tier Sandboxed Payload Viewer:** Safely executes HTML and Markdown artifacts via a fortified CSP, Bleach cleaning, DOMPurify, and restricted `<iframe>` sandboxing.
- 🔄 **Flexible Hybrid Model Uplink:** Runs completely offline via local **Ollama** (`llama3.2`, `mistral`, `gemma2`), with seamless automatic fallback to **Anthropic Claude** or **OpenAI GPT-4o**.
- 🎛️ **Cyberpunk / SOC Console Theme:** Split-pane desktop workstation with real-time uplink status, DB telemetry, and accessibility compliance (WCAG AA).

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Web Browser (:3000)                  │
│       React 18 + Vite + Tailwind + Zustand Console     │
└───────────────────────────┬────────────────────────────┘
                            │ REST / SSE
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Backend (:8000)               │
│                                                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────┐  │
│  │ Intent Router   │ │ Retrieval Svc   │ │ Sanitizer│  │
│  │ (QA/Essay/Art.) │ │ (Postgres FTS)  │ │ (Bleach) │  │
│  └────────┬────────┘ └────────┬────────┘ └────┬─────┘  │
└───────────┼───────────────────┼───────────────┼────────┘
            │                   │               │
  ┌─────────▼────────┐  ┌───────▼────────┐      │
  │  PostgreSQL 16   │  │   LLM Gateway  │      │
  │     (:5432)      │  │ (Ollama/Cloud) │◄─────┘
  │ Full-Text Search │  └───────┬────────┘
  │ tsvector/ts_rank │          │
  └──────────────────┘          ├─► Local Ollama (:11434)
                                └─► Anthropic / OpenAI APIs
```

---

## 📦 Prerequisites

| Tool | Recommended Version | Purpose |
|------|---------------------|---------|
| **Docker Desktop** | `≥ 4.x` (with Compose v2) | Runs PostgreSQL, Backend, and Frontend containers |
| **Ollama** | `≥ 0.3.x` | Host-based LLM engine (for local offline inference) |
| **Git** | `≥ 2.x` | Clones transcripts during ingestion |
| **Make** *(optional)* | Any | Command shortcuts (`make up`, `make ingest`, etc.) |

---

## 🚀 Quickstart

### 1. Clone & Configure Environment

```bash
git clone https://github.com/<your-username>/lenny-growth-assistant.git
cd lenny-growth-assistant

# Copy template configuration
cp .env.example .env
```

Review your `.env` settings. By default, it targets local Ollama:
```env
LLM_PROVIDER=ollama
MODEL_NAME=llama3.2
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### 2. Pull the Local Model

On your host machine, install [Ollama](https://ollama.com) and pull your preferred model:

```bash
ollama pull llama3.2
```

### 3. Spin Up Docker Containers

```bash
docker compose up --build -d
```

### 4. Ingest Podcast Transcripts

Populate the PostgreSQL database from the canonical transcript repository (`ChatPRD/lennys-podcast-transcripts`):

```bash
# Using Makefile
make ingest

# Or directly through Docker Compose
docker compose exec backend python -m app.ingest
```

### 5. Access the Console

Open your browser to:
👉 **`http://localhost:3000`**

---

## 🔀 Query Routing Engine

The assistant uses rule-based and semantic classification to route prompts to dedicated execution pipelines:

| Mode | Trigger Intent | Output Payload | Behavior |
|------|---------------|----------------|----------|
| **QA** *(Default)* | General questions, advice, strategies | Chat response with `[EP // Guest]` chips | Retrieves top-8 transcript chunks via PostgreSQL full-text search. Synthesizes strictly from retrieved context. |
| **ESSAY** | *"write a ship 30 essay"*, *"draft an essay on..."* | Formatted ~1,250-word essay in Payload Viewer | Applies the Ship 30 for 30 framework (clear hook, atomic ideas, actionable frameworks, cited guest insights). |
| **ARTIFACT** | *"generate html"*, *"create a dashboard"*, *"make markdown"* | Sandboxed HTML / Markdown viewer | Generates self-contained reports or dashboards, strictly sanitized against XSS. |

---

## 💬 Sample Prompts

### 🔍 Grounded Q&A
```text
What does Lenny and his guests say about retention curves and engagement loops?
How do top PLG companies structure their user activation funnels?
What are Brian Chesky's thoughts on functional vs. divisional org design?
```

### 📝 Ship 30 for 30 Essay
```text
Write a Ship 30 for 30 essay about why NPS is a lagging metric according to top growth leaders.
Draft an atomic essay about the difference between sales-led and product-led growth.
```

### 📊 Sandboxed Interactive Artifacts
```text
Generate an HTML dashboard displaying key retention metrics and benchmarks from the podcast.
Create a markdown cheat sheet of activation best practices.
```

---

## 🛡️ Security & Artifact Containment

Running LLM-generated code in the browser introduces significant XSS risks. This project implements a **defense-in-depth sanitization protocol**:

```
[Raw LLM Output]
       │
       ▼
1. Backend Sanitization (Python Bleach allowlist & regex script stripping)
       │
       ▼
2. Strict CSP Meta Tag Injection (default-src 'none'; style-src 'unsafe-inline'; img-src data:)
       │
       ▼
3. Client-Side Sanitization (DOMPurify HTML/SVG wash)
       │
       ▼
4. Sandboxed iframe Execution (sandbox="allow-same-origin", NO scripts, NO popups, NO forms)
```

Clicking the **`CONTAINMENT: ACTIVE`** badge in the UI reveals the exact sandbox security constraints currently enforced.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health status (PostgreSQL connection, LLM uplink, ingested chunk count) |
| `GET` | `/debug/status` | Current environment configuration & active provider |
| `POST` | `/api/v1/sessions` | Initializes a new conversation session |
| `GET` | `/api/v1/sessions/{id}/messages` | Fetches session conversation history |
| `POST` | `/api/v1/sessions/{id}/chat` | Sends message, executes routing, and streams/returns response |
| `GET` | `/api/v1/artifacts/{id}` | Retrieves generated HTML / Markdown payload |

Interactive Swagger documentation is available at **`http://localhost:8000/docs`**.

---

## 🧪 Testing

The test suite runs **100% offline** with fully mocked LLM providers:

```bash
# Run tests inside backend container
make test

# Or run locally with pytest
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt aiosqlite
pytest tests/ -v
```

### Test Coverage Highlights:
- ✅ **Sanitization Engine:** Validates that `<script>`, `onload`, `javascript:`, and iframe breakouts are purged.
- ✅ **Query Router:** Confirms accurate routing across QA, Essay, and Artifact intents.
- ✅ **Retrieval & Context Fallback:** Verifies that no-match queries trigger `"NO INTEL FOUND"`.
- ✅ **Provider Failover:** Validates automatic transition from local Ollama to cloud fallback when Ollama is unreachable.

---

## 📂 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── config.py           # Pydantic v2 settings & environment parsing
│   │   ├── database.py         # Async SQLAlchemy & connection pooling
│   │   ├── main.py             # FastAPI entrypoint & middleware
│   │   ├── ingest.py           # Transcript git-clone, chunker & FTS indexer
│   │   ├── models/             # Database ORM models & Pydantic schemas
│   │   ├── routers/            # Health, Sessions, Chat, and Artifact endpoints
│   │   ├── services/           # Router, Retrieval (ts_rank), LLM gateway, QA, Essay
│   │   └── skills/ship30/      # Ship 30 for 30 structural instructions
│   ├── db/
│   │   └── init.sql            # PostgreSQL schema, indices & tsvector definitions
│   └── tests/                  # Pytest offline test suite
├── frontend/
│   ├── src/
│   │   ├── components/         # BootSequence, StatusBar, ChatPanel, PayloadViewer
│   │   ├── hooks/              # useSession, useChat custom React hooks
│   │   ├── store/              # Zustand global state
│   │   ├── types/              # TypeScript interfaces
│   │   └── utils/              # API client & client-side DOMPurify sanitizer
│   ├── package.json
│   └── vite.config.ts
├── docs/                       # Product Requirements (PRD), Architecture & Test Plans
├── docker-compose.yml          # Postgres, Backend, and Frontend orchestration
├── Makefile                    # Developer CLI commands
└── .env.example                # Documented configuration template
```

---

## 🛠️ Common Troubleshooting

<details>
<summary><b>1. UPLINK: OFFLINE in UI status bar</b></summary>

Ensure Ollama is running on your host machine:
```bash
curl http://localhost:11434/api/tags
```
If using Linux, update `.env` to point to the host gateway bridge IP:
```env
OLLAMA_BASE_URL=http://172.17.0.1:11434
```
</details>

<details>
<summary><b>2. INDEX: EMPTY in status bar</b></summary>

The transcripts haven't been loaded into PostgreSQL yet. Run:
```bash
docker compose exec backend python -m app.ingest
```
</details>

<details>
<summary><b>3. Ollama timeout during Essay generation</b></summary>

Generating ~1,250 words on smaller CPUs can take 45–90 seconds. Increase the timeout in `.env`:
```env
LLM_TIMEOUT_SECONDS=180
```
</details>

<details>
<summary><b>4. Port 3000 or 8000 already in use</b></summary>

Modify the exposed host port in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Frontend
  - "8001:8000"  # Backend
```
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
<sub>Built for product builders and growth engineers. Transcripts courtesy of Lenny Rachitsky's Podcast.</sub>
</div>
