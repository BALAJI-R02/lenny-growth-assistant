"""QA pipeline: retrieval-augmented generation with strict citation grounding."""
from __future__ import annotations

import logging
from typing import Any

from app.models.schemas import Citation, ChunkResult
from app.services import llm
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

NO_INTEL_MSG = (
    "**NO INTEL FOUND** in the transcripts for your query.\n\n"
    "The Lenny Growth Assistant only answers from retrieved transcript evidence. "
    "No relevant passages were found. Try rephrasing your question with different keywords, "
    "or ask about topics covered in Lenny's Podcast."
)

_QA_SYSTEM = """\
You are the Lenny Growth Assistant, an expert analyst of Lenny Rachitsky's podcast transcripts.

STRICT RULES:
1. Answer ONLY from the provided transcript excerpts (EVIDENCE SOURCES below).
2. Every claim MUST be cited as [1], [2], etc. referencing the numbered sources.
3. Do NOT introduce information not present in the sources.
4. Do NOT say "I think" or "In my opinion" — only report what the transcripts say.
5. Use clear, structured prose: lead with the key insight, support with evidence.
6. If sources partially answer the question, say so and cite what you have.
7. Keep responses concise: 200-400 words unless the question requires more.
"""


def _build_context(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(
            f"[{i}] Episode: {chunk.episode} | Guest: {chunk.guest or 'Unknown'}\n"
            f"Path: {chunk.source_path}\n"
            f"---\n{chunk.text}\n"
        )
    return "\n\n".join(lines)


async def answer(
    question: str,
    chunks: list[RetrievedChunk],
    history: list[dict[str, Any]] | None = None,
) -> tuple[str, list[Citation], str, str]:
    """
    Generate a grounded answer from retrieved chunks.

    Returns: (content, citations, provider, model)
    """
    if not chunks:
        return NO_INTEL_MSG, [], "", ""

    context = _build_context(chunks)
    messages: list[dict] = [{"role": "system", "content": _QA_SYSTEM}]

    # Add recent history for multi-turn context (last 4 messages)
    if history:
        for h in history[-4:]:
            messages.append({"role": h["role"], "content": h["content"][:500]})

    user_msg = f"""EVIDENCE SOURCES:
{context}

QUESTION: {question}

Answer based strictly on the evidence above. Cite sources as [1], [2], etc."""

    messages.append({"role": "user", "content": user_msg})

    content, provider_used, model_used = await llm.complete(messages)

    # Build citation objects from referenced chunks
    citations = []
    for i, chunk in enumerate(chunks, 1):
        if f"[{i}]" in content:
            citations.append(
                Citation(
                    ref=i,
                    episode=chunk.episode,
                    guest=chunk.guest or "Unknown",
                    source_path=chunk.source_path,
                    snippet=chunk.text[:300] + ("..." if len(chunk.text) > 300 else ""),
                )
            )

    return content, citations, provider_used, model_used


def chunks_to_schema(chunks: list[RetrievedChunk]) -> list[ChunkResult]:
    return [
        ChunkResult(
            id=c.id,
            episode=c.episode,
            guest=c.guest,
            source_path=c.source_path,
            text=c.text[:400],
            score=c.score,
        )
        for c in chunks
    ]
