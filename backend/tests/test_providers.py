"""Tests: provider switching, error contracts, LLM unavailable."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm import LLMUnavailableError


@pytest.mark.asyncio
async def test_llm_unavailable_error_is_raised():
    """LLMUnavailableError is a RuntimeError with a code attribute."""
    err = LLMUnavailableError("Ollama down", code="LLM_UNAVAILABLE")
    assert isinstance(err, RuntimeError)
    assert err.code == "LLM_UNAVAILABLE"
    assert "Ollama down" in str(err)


@pytest.mark.asyncio
async def test_chat_endpoint_returns_structured_error_on_llm_failure(client):
    """Chat endpoint returns structured JSON error when LLM unavailable.

    We patch qa.answer (not llm.complete) because empty retrieval short-circuits
    before llm.complete is called — qa.answer is the actual LLM call site.
    """
    from app.services.retrieval import RetrievedChunk

    fake_chunk = RetrievedChunk(
        id="test-id",
        episode="ep-test",
        guest="Test Guest",
        source_path="test.md",
        text="Some transcript text about retention",
        score=0.5,
    )

    with patch("app.services.retrieval.retrieve", new_callable=AsyncMock, return_value=[fake_chunk]):
        with patch(
            "app.services.qa.answer",
            new_callable=AsyncMock,
            side_effect=LLMUnavailableError("Ollama unreachable and no cloud fallback configured."),
        ):
            resp = await client.post("/api/v1/sessions")
            session_id = resp.json()["id"]

            chat_resp = await client.post(
                f"/api/v1/sessions/{session_id}/chat",
                json={"content": "What does Lenny say about retention?"},
            )

    assert chat_resp.status_code in (503, 500)
    data = chat_resp.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "request_id" in data["error"]


@pytest.mark.asyncio
async def test_chat_endpoint_returns_error_for_invalid_session(client):
    """Chat to nonexistent session returns 404."""
    resp = await client.post(
        "/api/v1/sessions/00000000-0000-0000-0000-000000000000/chat",
        json={"content": "test"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_no_intel_found_on_empty_retrieval(client):
    """When retrieval is empty, response includes NO INTEL FOUND."""
    with patch("app.services.retrieval.retrieve", new_callable=AsyncMock, return_value=[]):
        with patch(
            "app.services.qa.answer",
            new_callable=AsyncMock,
            return_value=(
                "**NO INTEL FOUND** in the transcripts for your query.",
                [],
                "mock",
                "mock-model",
            ),
        ):
            resp = await client.post("/api/v1/sessions")
            session_id = resp.json()["id"]

            chat_resp = await client.post(
                f"/api/v1/sessions/{session_id}/chat",
                json={"content": "What is 2+2?"},
            )

    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "NO INTEL FOUND" in data["content"]


@pytest.mark.asyncio
async def test_chat_message_has_route_field(client):
    """Chat response includes route classification."""
    with patch("app.services.retrieval.retrieve", new_callable=AsyncMock, return_value=[]):
        with patch(
            "app.services.qa.answer",
            new_callable=AsyncMock,
            return_value=("Answer [1]", [], "mock", "mock-model"),
        ):
            resp = await client.post("/api/v1/sessions")
            session_id = resp.json()["id"]

            chat_resp = await client.post(
                f"/api/v1/sessions/{session_id}/chat",
                json={"content": "What does Lenny say about activation?"},
            )

    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["route"] == "QA"


@pytest.mark.asyncio
async def test_chat_essay_route_detected(client):
    """Essay keyword triggers ESSAY route."""
    with patch("app.services.retrieval.retrieve", new_callable=AsyncMock, return_value=[]):
        with patch(
            "app.services.essay.generate",
            new_callable=AsyncMock,
            return_value=("# Essay\n\n" + "Word. " * 1250, [], "mock", "mock-model", 1250),
        ):
            resp = await client.post("/api/v1/sessions")
            session_id = resp.json()["id"]

            chat_resp = await client.post(
                f"/api/v1/sessions/{session_id}/chat",
                json={"content": "Write an essay about product-led growth"},
            )

    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["route"] == "ESSAY"
    assert data["artifact_id"] is not None
