"""Artifacts router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import Artifact
from app.models.schemas import ArtifactOut

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)) -> ArtifactOut:
    """Fetch artifact metadata + sanitized content."""
    artifact = await db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ArtifactOut.model_validate(artifact)


@router.get("/{artifact_id}/raw", response_class=PlainTextResponse)
async def get_artifact_raw(artifact_id: str, db: AsyncSession = Depends(get_db)) -> str:
    """Return raw artifact content for download."""
    artifact = await db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.content
