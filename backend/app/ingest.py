"""
Idempotent ingest script for Lenny's Podcast transcripts.

Usage:
  python -m app.ingest

Environment variables (from .env):
  TRANSCRIPTS_REPO_URL  — GitHub repo URL
  INGEST_MAX_EPISODES   — Max episodes to ingest (0 = unlimited)
  CHUNK_SIZE_TOKENS     — Target chunk size in tokens
  CHUNK_OVERLAP_TOKENS  — Overlap between chunks
  DATABASE_URL          — Postgres connection string
"""
from __future__ import annotations

import asyncio
import logging
import re
import sys
import tempfile
import time
from pathlib import Path

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── Tokenization (approximate; tiktoken for accuracy) ─────────────────────


def _estimate_tokens(text: str) -> int:
    """Rough token count: ~4 chars per token."""
    return len(text) // 4


def _chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping chunks by approximate token count.
    Tries to split on sentence boundaries.
    """
    # Split into sentences (rough)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = _estimate_tokens(sent)
        if current_tokens + sent_tokens > chunk_size and current:
            chunk_text = " ".join(current)
            chunks.append(chunk_text.strip())
            # Overlap: keep last N tokens worth of sentences
            overlap_sents: list[str] = []
            overlap_tokens = 0
            for s in reversed(current):
                t = _estimate_tokens(s)
                if overlap_tokens + t > overlap:
                    break
                overlap_sents.insert(0, s)
                overlap_tokens += t
            current = overlap_sents
            current_tokens = overlap_tokens
        current.append(sent)
        current_tokens += sent_tokens

    if current:
        chunks.append(" ".join(current).strip())

    return [c for c in chunks if len(c.strip()) > 50]


# ── Metadata extraction ────────────────────────────────────────────────────


def _extract_metadata(filepath: Path) -> tuple[str, str]:
    """
    Extract episode name and guest from file path / frontmatter.
    Returns: (episode, guest)
    """
    stem = filepath.stem  # e.g., "ep-123-brian-balfour" or "123_retention_loops"

    # Try YAML frontmatter
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        if content.startswith("---"):
            fm_end = content.find("---", 3)
            if fm_end > 0:
                fm = content[3:fm_end]
                guest_match = re.search(r"guest:\s*(.+)", fm, re.IGNORECASE)
                ep_match = re.search(r"episode:\s*(.+)", fm, re.IGNORECASE)
                guest = guest_match.group(1).strip().strip('"').strip("'") if guest_match else ""
                episode = ep_match.group(1).strip().strip('"').strip("'") if ep_match else stem
                return episode, guest
    except Exception:
        pass

    # Fallback: parse from filename
    # e.g., "how-brian-balfour-thinks-about-retention"
    episode = stem.replace("-", " ").replace("_", " ").title()
    guest = ""
    return episode, guest


def _extract_text(filepath: Path) -> str:
    """Read transcript file, strip markdown syntax for FTS."""
    try:
        raw = filepath.read_text(encoding="utf-8", errors="ignore")
        # Remove YAML frontmatter
        if raw.startswith("---"):
            end = raw.find("---", 3)
            if end > 0:
                raw = raw[end + 3:]
        # Strip markdown headers (keep text)
        raw = re.sub(r"^#{1,6}\s+", "", raw, flags=re.MULTILINE)
        # Strip markdown links but keep text
        raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
        # Strip HTML tags
        raw = re.sub(r"<[^>]+>", " ", raw)
        return raw.strip()
    except Exception as e:
        logger.warning(f"Could not read {filepath}: {e}")
        return ""


# ── Database upsert ───────────────────────────────────────────────────────


async def _upsert_chunks(
    conn: asyncpg.Connection,
    episode: str,
    guest: str,
    source_path: str,
    chunks: list[str],
) -> int:
    """Upsert chunks idempotently. Returns count inserted/updated."""
    inserted = 0
    for idx, chunk_text in enumerate(chunks):
        await conn.execute(
            """
            INSERT INTO chunks (id, episode, guest, source_path, chunk_index, text)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)
            ON CONFLICT (source_path, chunk_index)
            DO UPDATE SET text = EXCLUDED.text, episode = EXCLUDED.episode, guest = EXCLUDED.guest
            """,
            episode,
            guest,
            source_path,
            idx,
            chunk_text,
        )
        inserted += 1
    return inserted


# ── Main ingest ───────────────────────────────────────────────────────────


async def run_ingest() -> None:
    start = time.time()
    logger.info("Starting ingest", extra={"repo": settings.transcripts_repo_url})

    # Parse DB URL for asyncpg (strip driver prefix)
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    # Clone or use cached repo
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "transcripts"
        logger.info(f"Cloning {settings.transcripts_repo_url} ...")

        import subprocess
        result = subprocess.run(
            ["git", "clone", "--depth=1", settings.transcripts_repo_url, str(repo_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error(f"Git clone failed: {result.stderr}")
            sys.exit(1)

        logger.info("Clone complete")

        # Find markdown files
        md_files = sorted(repo_dir.rglob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files")

        # Cap episodes
        max_ep = settings.ingest_max_episodes
        if max_ep > 0 and len(md_files) > max_ep:
            md_files = md_files[:max_ep]
            logger.info(f"Capped to {max_ep} episodes")

        # Connect to DB
        conn = await asyncpg.connect(db_url)

        total_files = 0
        total_chunks = 0
        skipped = 0

        for filepath in md_files:
            episode, guest = _extract_metadata(filepath)
            text = _extract_text(filepath)

            if len(text) < 100:
                skipped += 1
                continue

            chunks = _chunk_text(
                text,
                chunk_size=settings.chunk_size_tokens,
                overlap=settings.chunk_overlap_tokens,
            )

            # Use relative path as source_path
            try:
                rel_path = str(filepath.relative_to(repo_dir))
            except ValueError:
                rel_path = str(filepath)

            n = await _upsert_chunks(conn, episode, guest, rel_path, chunks)
            total_chunks += n
            total_files += 1

            if total_files % 10 == 0:
                logger.info(f"Progress: {total_files}/{len(md_files)} files, {total_chunks} chunks")

        await conn.close()

    elapsed = time.time() - start
    logger.info(
        f"Ingest complete: {total_files} files, {total_chunks} chunks, {skipped} skipped, "
        f"{elapsed:.1f}s",
        extra={
            "total_files": total_files,
            "total_chunks": total_chunks,
            "skipped": skipped,
            "elapsed_s": round(elapsed, 1),
        },
    )


if __name__ == "__main__":
    asyncio.run(run_ingest())
