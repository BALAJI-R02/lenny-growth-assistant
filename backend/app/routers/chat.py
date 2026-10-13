"""Main chat endpoint — routes messages to QA, ESSAY, or ARTIFACT pipelines."""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import Artifact, Message, Session
from app.models.schemas import ArtifactOut, ChatRequest, MessageOut
from app.services import artifact as artifact_svc
from app.services import essay as essay_svc
from app.services import qa as qa_svc
from app.services.llm import LLMUnavailableError
from app.services.query_rewriter import rewrite
from app.services.retrieval import retrieve
from app.services.router import Route, classify

router = APIRouter(prefix="/api/v1/sessions", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/{session_id}/chat")
async def chat(
    session_id: str,
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Main chat endpoint. Routes to QA, ESSAY, or ARTIFACT."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Verify session
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Persist user message
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=body.content,
        citations=[],
    )
    db.add(user_msg)
    await db.commit()

    # Load recent history for context
    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history_msgs = list(reversed(history_result.scalars().all()))
    history = [{"role": m.role, "content": m.content} for m in history_msgs]

    # Classify route
    route = classify(body.content)

    logger.info(
        "Chat request",
        extra={
            "request_id": request_id,
            "session_id": session_id,
            "route": route.value,
        },
    )

    try:
        content = ""
        citations = []
        provider_used = ""
        model_used = ""
        artifact_id = None
        retrieval_chunks = []

        if route == Route.QA:
            # Rewrite follow-up queries (exclude the current user msg we just added)
            prior_history = [h for h in history if not (h["role"] == "user" and h["content"] == body.content)]
            search_query = await rewrite(body.content, prior_history[-6:])

            # Retrieve chunks
            chunks = await retrieve(search_query, db)
            retrieval_chunks = qa_svc.chunks_to_schema(chunks)

            # Generate answer
            content, citations, provider_used, model_used = await qa_svc.answer(
                body.content, chunks, history
            )

        elif route == Route.ESSAY:
            # Extract topic (strip trigger keywords)
            topic = body.content
            for kw in [
                "write a ship 30 for 30 essay about",
                "write a ship30 essay about",
                "ship 30 essay about",
                "write an essay about",
                "draft an essay about",
            ]:
                lower = topic.lower()
                idx = lower.find(kw)
                if idx != -1:
                    topic = topic[idx + len(kw):].strip()
                    break
            if not topic or len(topic) < 3:
                topic = body.content

            chunks = await retrieve(topic, db)
            retrieval_chunks = qa_svc.chunks_to_schema(chunks)

            content, citations, provider_used, model_used, word_count = await essay_svc.generate(
                topic, chunks
            )

            artifact_title = f"Ship30 Essay: {topic[:50]}"
            artifact_obj = Artifact(
                session_id=session_id,
                type="markdown",
                title=artifact_title,
                content=content,
            )
            db.add(artifact_obj)
            await db.flush()
            artifact_id = artifact_obj.id
            content = (
                f"{content}\n\n---\n"
                f"*Word count: {word_count} | Essay saved to PAYLOAD VIEWER*"
            )

        elif route == Route.ARTIFACT:
            chunks = await retrieve(body.content, db)
            retrieval_chunks = qa_svc.chunks_to_schema(chunks)

            art_type = artifact_svc.infer_type(body.content)
            art_title = artifact_svc.infer_title(body.content, art_type)

            ctx = "\n".join(
                f"{h['role'].upper()}: {h['content'][:200]}"
                for h in history[-4:]
            )

            _, sanitized, provider_used, model_used = await artifact_svc.generate(
                request=body.content,
                artifact_type=art_type,
                chunks=chunks if chunks else None,
                conversation_context=ctx,
            )

            artifact_obj = Artifact(
                session_id=session_id,
                type=art_type,
                title=art_title,
                content=sanitized,
            )
            db.add(artifact_obj)
            await db.flush()
            artifact_id = artifact_obj.id
            content = (
                f"✅ **{art_title}** has been generated and sent to the PAYLOAD VIEWER.\n\n"
                f"*Type: {art_type.upper()} | Security: CONTAINMENT ACTIVE*"
            )

    except LLMUnavailableError as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"LLM unavailable: {e}",
            extra={
                "request_id": request_id,
                "session_id": session_id,
                "error_type": e.code,
                "latency_ms": latency_ms,
            },
        )
        err_msg = Message(
            session_id=session_id,
            role="assistant",
            content=f"⚠️ **UPLINK FAILURE**: {str(e)}",
            citations=[],
            route=route.value,
            latency_ms=latency_ms,
        )
        db.add(err_msg)
        await db.commit()
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": e.code,
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"Chat error: {e}",
            extra={
                "request_id": request_id,
                "session_id": session_id,
                "error_type": "INTERNAL_ERROR",
                "latency_ms": latency_ms,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )

    latency_ms = int((time.time() - start_time) * 1000)

    citations_json = [c.model_dump() for c in citations]
    assistant_msg = Message(
        session_id=session_id,
        role="assistant",
        content=content,
        citations=citations_json,
        route=route.value,
        provider=provider_used,
        model=model_used,
        latency_ms=latency_ms,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    logger.info(
        "Chat complete",
        extra={
            "request_id": request_id,
            "session_id": session_id,
            "route": route.value,
            "provider": provider_used,
            "model": model_used,
            "latency_ms": latency_ms,
            "hit_count": len(retrieval_chunks),
        },
    )

    return MessageOut(
        id=assistant_msg.id,
        session_id=session_id,
        role="assistant",
        content=content,
        citations=citations,
        route=route.value,
        provider=provider_used,
        model=model_used,
        latency_ms=latency_ms,
        artifact_id=artifact_id,
        retrieval_chunks=retrieval_chunks,
        created_at=assistant_msg.created_at,
    )


@router.get("/{session_id}/artifacts", response_model=list[ArtifactOut])
async def list_artifacts(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[ArtifactOut]:
    """List all artifacts for a session."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Artifact)
        .where(Artifact.session_id == session_id)
        .order_by(Artifact.created_at.desc())
    )
    artifacts = result.scalars().all()
    return [ArtifactOut.model_validate(a) for a in artifacts]
