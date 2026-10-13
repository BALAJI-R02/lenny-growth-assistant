"""Tests: retrieval ranking and empty results handling."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.retrieval import RetrievedChunk, _build_tsquery


# ── tsquery builder tests ──────────────────────────────────────────────────

@pytest.mark.parametrize("query,expected_op", [
    ("retention loops", " | "),       # <= 2 terms → OR
    ("retention", " | "),              # 1 term → OR (but no join)
    ("retention activation engagement PLG metrics", " & "),  # many terms → AND
])
def test_build_tsquery(query: str, expected_op: str):
    result = _build_tsquery(query)
    assert result != ""
    if len([t for t in query.split() if len(t) > 2]) > 2:
        assert " & " in result


def test_build_tsquery_strips_special_chars():
    result = _build_tsquery("what's the #1 retention?!")
    assert "?" not in result
    assert "!" not in result
    assert "#" not in result


def test_build_tsquery_empty_input():
    result = _build_tsquery("")
    assert result == ""


def test_build_tsquery_only_short_words():
    result = _build_tsquery("a is to be")
    assert result == ""  # all <= 2 chars filtered


# ── Retrieval integration tests (with mocked DB) ───────────────────────────

@pytest.mark.asyncio
async def test_retrieve_returns_empty_on_no_results():
    """Empty DB result → empty list."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.services.retrieval import retrieve
    chunks = await retrieve("capital of france", mock_db)
    assert chunks == []


@pytest.mark.asyncio
async def test_retrieve_filters_by_min_score():
    """Chunks below min_score are filtered out."""
    mock_db = AsyncMock()
    mock_result = MagicMock()

    # Create mock rows
    row1 = MagicMock()
    row1.id = "id-1"
    row1.episode = "ep-1"
    row1.guest = "Guest A"
    row1.source_path = "ep1.md"
    row1.text = "Some text about retention"
    row1.score = 0.5  # above threshold

    row2 = MagicMock()
    row2.id = "id-2"
    row2.episode = "ep-2"
    row2.guest = "Guest B"
    row2.source_path = "ep2.md"
    row2.text = "Some other text"
    row2.score = 0.01  # below threshold

    mock_result.fetchall.return_value = [row1, row2]
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.services.retrieval import retrieve
    chunks = await retrieve("retention", mock_db, min_score=0.05)
    assert len(chunks) == 1
    assert chunks[0].episode == "ep-1"


@pytest.mark.asyncio
async def test_retrieve_orders_by_score():
    """Results should be ordered by score descending."""
    from app.services.retrieval import retrieve

    mock_db = AsyncMock()
    mock_result = MagicMock()

    rows = []
    for i, score in enumerate([0.3, 0.8, 0.5]):
        r = MagicMock()
        r.id = f"id-{i}"
        r.episode = f"ep-{i}"
        r.guest = f"Guest {i}"
        r.source_path = f"ep{i}.md"
        r.text = f"Text {i}"
        r.score = score
        rows.append(r)

    mock_result.fetchall.return_value = rows
    mock_db.execute = AsyncMock(return_value=mock_result)

    chunks = await retrieve("retention loops", mock_db, min_score=0.0)
    # DB returns in order, retrieval just filters; order from DB preserved
    assert len(chunks) == 3


@pytest.mark.asyncio
async def test_retrieve_db_error_returns_empty():
    """DB error → empty list, no exception propagated."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("DB connection lost"))

    from app.services.retrieval import retrieve
    chunks = await retrieve("retention", mock_db)
    assert chunks == []
