"""Pydantic v2 request/response schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Citations ──────────────────────────────────────────────────────────────


class Citation(BaseModel):
    ref: int
    episode: str
    guest: str
    source_path: str
    snippet: str


# ── Chunks ─────────────────────────────────────────────────────────────────


class ChunkResult(BaseModel):
    id: str
    episode: str
    guest: str
    source_path: str
    text: str
    score: float


# ── Messages ───────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10_000)


class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: list[Citation] = []
    route: str | None = None
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    artifact_id: str | None = None
    retrieval_chunks: list[ChunkResult] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Sessions ───────────────────────────────────────────────────────────────


class SessionOut(BaseModel):
    id: str
    created_at: datetime
    user_meta: dict[str, Any] = {}

    model_config = {"from_attributes": True}


# ── Artifacts ──────────────────────────────────────────────────────────────


class ArtifactOut(BaseModel):
    id: str
    session_id: str
    type: str
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Health ─────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    db: str
    llm: str
    index: str
    chunk_count: int
    provider: str
    model: str
    fallback_available: bool


class DebugStatus(BaseModel):
    provider: str
    model: str
    ollama_base_url: str
    chunk_count: int
    retrieval_top_k: int
    retrieval_min_score: float
    has_cloud_fallback: bool
    fallback_provider: str | None


# ── Errors ─────────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
