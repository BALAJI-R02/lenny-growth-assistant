"""FastAPI application factory with middleware and routing."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import artifacts, chat, health, sessions


# ── Structured JSON logging ────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    EXTRA_FIELDS = [
        "request_id", "session_id", "route", "provider", "model",
        "latency_ms", "hit_count", "error_type", "word_count",
        "content_length", "tsquery",
    ]

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        for key in self.EXTRA_FIELDS:
            val = getattr(record, key, None)
            if val is not None:
                log_data[key] = val
        return json.dumps(log_data)


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


_configure_logging()
logger = logging.getLogger(__name__)

# ── App factory ────────────────────────────────────────────────────────────

app = FastAPI(
    title="Lenny Growth Assistant API",
    description="RAG-powered product/growth Q&A grounded in Lenny's Podcast transcripts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Inject request_id into every response for distributed tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id, "error_type": type(exc).__name__},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
            }
        },
    )


# ── Routers ────────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(artifacts.router)


@app.get("/")
async def root():
    return {
        "service": "Lenny Growth Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
