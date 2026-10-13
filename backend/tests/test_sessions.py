"""Tests: session creation, isolation, and message persistence."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_create_session(client):
    """Can create a new session."""
    resp = await client.post("/api/v1/sessions")
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "created_at" in data
    # ID should be a UUID-format string
    assert len(data["id"]) == 36


@pytest.mark.asyncio
async def test_get_session(client):
    """Can retrieve a created session."""
    create_resp = await client.post("/api/v1/sessions")
    session_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == session_id


@pytest.mark.asyncio
async def test_session_not_found(client):
    """Unknown session ID returns 404."""
    resp = await client.get("/api/v1/sessions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_session_messages_empty(client):
    """New session has empty messages list."""
    create_resp = await client.post("/api/v1/sessions")
    session_id = create_resp.json()["id"]

    msgs_resp = await client.get(f"/api/v1/sessions/{session_id}/messages")
    assert msgs_resp.status_code == 200
    assert msgs_resp.json() == []


@pytest.mark.asyncio
async def test_session_isolation(client):
    """Messages from session A do not appear in session B."""
    with patch("app.services.retrieval.retrieve", new_callable=AsyncMock, return_value=[]):
        with patch("app.services.qa.answer", new_callable=AsyncMock,
                   return_value=("Test answer [1]", [], "mock", "mock-model")):
            # Create two sessions
            resp_a = await client.post("/api/v1/sessions")
            resp_b = await client.post("/api/v1/sessions")
            sid_a = resp_a.json()["id"]
            sid_b = resp_b.json()["id"]

            # Send message to session A only
            await client.post(
                f"/api/v1/sessions/{sid_a}/chat",
                json={"content": "What about retention?"},
            )

            # Session B should still be empty
            msgs_b = await client.get(f"/api/v1/sessions/{sid_b}/messages")
            assert msgs_b.json() == []

            # Session A should have messages (user + assistant)
            msgs_a = await client.get(f"/api/v1/sessions/{sid_a}/messages")
            assert len(msgs_a.json()) >= 1


@pytest.mark.asyncio
async def test_message_persistence(client):
    """Messages are persisted and retrievable after being sent."""
    with patch("app.services.retrieval.retrieve", new_callable=AsyncMock, return_value=[]):
        with patch("app.services.qa.answer", new_callable=AsyncMock,
                   return_value=("Test answer about growth [1]", [], "mock", "mock-model")):
            resp = await client.post("/api/v1/sessions")
            session_id = resp.json()["id"]

            # Send a message
            chat_resp = await client.post(
                f"/api/v1/sessions/{session_id}/chat",
                json={"content": "What does Lenny say about growth?"},
            )
            assert chat_resp.status_code == 200

            # Load history — should have user + assistant
            msgs = await client.get(f"/api/v1/sessions/{session_id}/messages")
            msgs_data = msgs.json()
            assert len(msgs_data) >= 2
            roles = [m["role"] for m in msgs_data]
            assert "user" in roles
            assert "assistant" in roles


@pytest.mark.asyncio
async def test_chat_requires_valid_session(client):
    """Chat to nonexistent session returns 404."""
    resp = await client.post(
        "/api/v1/sessions/nonexistent-session-id/chat",
        json={"content": "test"},
    )
    assert resp.status_code == 404
