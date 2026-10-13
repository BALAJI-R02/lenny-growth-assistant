"""Health and debug status endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.schemas import DebugStatus, HealthResponse
from app.services import llm
from app.services.retrieval import count_chunks

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Overall system health check."""
    db_status = "ok"
    chunk_count = 0
    try:
        await db.execute(text("SELECT 1"))
        chunk_count = await count_chunks(db)
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        db_status = "down"

    llm_ok, llm_detail = await llm.check_health()
    llm_status = "ok" if llm_ok else "down"
    index_status = "ok" if chunk_count > 0 else "empty"
    overall = "ok" if db_status == "ok" and llm_ok else "degraded"

    return HealthResponse(
        status=overall,
        db=db_status,
        llm=llm_status,
        index=index_status,
        chunk_count=chunk_count,
        provider=settings.llm_provider,
        model=settings.model_name,
        fallback_available=settings.has_cloud_fallback,
    )


@router.get("/debug/status", response_model=DebugStatus)
async def debug_status(db: AsyncSession = Depends(get_db)) -> DebugStatus:
    """Detailed debug info (development only)."""
    chunk_count = 0
    try:
        chunk_count = await count_chunks(db)
    except Exception:
        pass

    return DebugStatus(
        provider=settings.llm_provider,
        model=settings.model_name,
        ollama_base_url=settings.ollama_base_url,
        chunk_count=chunk_count,
        retrieval_top_k=settings.retrieval_top_k,
        retrieval_min_score=settings.retrieval_min_score,
        has_cloud_fallback=settings.has_cloud_fallback,
        fallback_provider=settings.fallback_provider,
    )
