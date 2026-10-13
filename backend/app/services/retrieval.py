"""Postgres full-text search retrieval service."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    id: str
    episode: str
    guest: str
    source_path: str
    text: str
    score: float


def _build_tsquery(query: str) -> str:
    """
    Convert a natural language query to a PostgreSQL tsquery string.
    Strips stop words and joins key terms with |.
    """
    STOP_WORDS = {
        "what", "does", "lenny", "say", "about", "and", "the", "for", "with",
        "how", "can", "why", "are", "tell", "explain", "give", "growth", "assistant"
    }
    clean = re.sub(r"[^\w\s-]", " ", query)
    tokens = [t.strip().lower() for t in clean.split() if len(t.strip()) > 2]
    keywords = [t for t in tokens if t not in STOP_WORDS]
    if not keywords:
        keywords = tokens
    if not keywords:
        return ""
    return " | ".join(keywords)


async def retrieve(
    query: str,
    db: AsyncSession,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[RetrievedChunk]:
    """
    Full-text search over transcript chunks.

    Returns chunks ordered by ts_rank DESC.
    Empty list if no results or max_score < min_score.
    """
    top_k = top_k or settings.retrieval_top_k
    min_score = min_score if min_score is not None else settings.retrieval_min_score

    tsquery = _build_tsquery(query)
    if not tsquery:
        logger.warning("Empty tsquery after preprocessing", extra={"query": query})
        return []

    sql = text(
        """
        SELECT
            id::text,
            episode,
            guest,
            source_path,
            text,
            ts_rank(tsv, to_tsquery('english', :q)) AS score
        FROM chunks
        WHERE tsv @@ to_tsquery('english', :q)
        ORDER BY score DESC
        LIMIT :limit
        """
    )

    try:
        result = await db.execute(sql, {"q": tsquery, "limit": top_k})
        rows = result.fetchall()
    except Exception as e:
        logger.error(f"Retrieval query failed: {e}", extra={"tsquery": tsquery})
        return []

    chunks = [
        RetrievedChunk(
            id=row.id,
            episode=row.episode,
            guest=row.guest,
            source_path=row.source_path,
            text=row.text,
            score=float(row.score),
        )
        for row in rows
    ]

    # Filter by minimum score
    chunks = [c for c in chunks if c.score >= min_score]

    logger.info(
        "Retrieval complete",
        extra={
            "query": query,
            "tsquery": tsquery,
            "hit_count": len(chunks),
            "max_score": chunks[0].score if chunks else 0.0,
        },
    )

    return chunks


async def count_chunks(db: AsyncSession) -> int:
    """Return total number of indexed chunks."""
    result = await db.execute(text("SELECT COUNT(*) FROM chunks"))
    return result.scalar() or 0
