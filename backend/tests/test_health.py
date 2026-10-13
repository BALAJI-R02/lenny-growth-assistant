"""Tests: health endpoint, DB status, LLM status, index status."""
from __future__ import annotations

from unittest.mock import patch, AsyncMock

import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    """Health returns ok when all systems up."""
    with patch("app.routers.health.count_chunks", new_callable=AsyncMock, return_value=100):
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["chunk_count"] == 100


@pytest.mark.asyncio
async def test_health_structure(client):
    """Health response has all required fields."""
    with patch("app.routers.health.count_chunks", new_callable=AsyncMock, return_value=0):
        resp = await client.get("/health")
    data = resp.json()
    required_keys = {"status", "db", "llm", "index", "chunk_count", "provider", "model"}
    assert required_keys.issubset(data.keys())


@pytest.mark.asyncio
async def test_health_empty_index(client):
    """Health shows empty index status when no chunks."""
    with patch("app.routers.health.count_chunks", new_callable=AsyncMock, return_value=0):
        resp = await client.get("/health")
    assert resp.json()["index"] == "empty"


@pytest.mark.asyncio
async def test_health_llm_down(client):
    """Health shows llm:down when provider unreachable."""
    # Override the client-level mock with a 'down' response
    with patch("app.services.llm.check_health", return_value=(False, "connection refused")):
        with patch("app.routers.health.count_chunks", new_callable=AsyncMock, return_value=100):
            resp = await client.get("/health")
    data = resp.json()
    assert data["llm"] == "down"
    assert data["status"] == "degraded"


@pytest.mark.asyncio
async def test_debug_status(client):
    """Debug status returns provider and config info."""
    with patch("app.routers.health.count_chunks", new_callable=AsyncMock, return_value=42):
        resp = await client.get("/debug/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "model" in data
    assert "chunk_count" in data
    assert data["chunk_count"] == 42
