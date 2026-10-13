"""Session management router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import Message, Session
from app.models.schemas import MessageOut, SessionOut

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(db: AsyncSession = Depends(get_db)) -> SessionOut:
    """Create a new session (OPERATION)."""
    session = Session()
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionOut.model_validate(session)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)) -> SessionOut:
    """Get session metadata."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut.model_validate(session)


@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[MessageOut]:
    """Load full conversation history for a session."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        MessageOut(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            route=m.route,
            provider=m.provider,
            model=m.model,
            latency_ms=m.latency_ms,
            artifact_id=None,
            retrieval_chunks=[],
            created_at=m.created_at,
        )
        for m in messages
    ]
