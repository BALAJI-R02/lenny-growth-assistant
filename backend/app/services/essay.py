"""Essay pipeline: Ship 30 for 30 style essay generation with word count enforcement."""
from __future__ import annotations

import logging
from pathlib import Path

from app.models.schemas import Citation
from app.services import llm
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "ship30" / "SKILL.md"

TARGET_WORDS = 1250
MIN_WORDS = 1150
MAX_WORDS = 1350


def _load_skill() -> str:
    try:
        return _SKILL_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"SKILL.md not found at {_SKILL_PATH}")
        return "Write a ~1,250-word essay with a strong hook, clear structure, and specific takeaway."


def _count_words(text: str) -> int:
    return len(text.split())


def _build_evidence_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No transcript evidence available. Write from general product/growth knowledge."
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(
            f"[{i}] Episode: {c.episode} | Guest: {c.guest or 'Unknown'}\n"
            f"Path: {c.source_path}\n---\n{c.text}\n"
        )
    return "\n\n".join(lines)


async def generate(
    topic: str,
    chunks: list[RetrievedChunk],
) -> tuple[str, list[Citation], str, str, int]:
    """
    Generate a Ship 30 for 30 style essay on the given topic.

    Returns: (content, citations, provider, model, word_count)
    """
    skill_guide = _load_skill()
    evidence = _build_evidence_context(chunks)

    system_prompt = f"""You are an expert digital writer following Ship 30 for 30 principles.

{skill_guide}

EVIDENCE SOURCES (cite these as [1], [2], etc. — REQUIRED):
{evidence}
"""

    user_prompt = f"""Write a Ship 30 for 30 essay on this topic: **{topic}**

Requirements:
- Target word count: EXACTLY {TARGET_WORDS} words (acceptable range: {MIN_WORDS}-{MAX_WORDS})
- Follow the essay structure template in your instructions
- Include ALL items from the quality checklist
- Cite evidence as [1], [2], [3] from the EVIDENCE SOURCES above
- DO NOT add a word count at the end — I will count it automatically

Begin writing now:"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    content, provider_used, model_used = await llm.complete(messages, timeout=600)
    word_count = _count_words(content)

    logger.info(
        f"Essay generated: {word_count} words",
        extra={"topic": topic, "word_count": word_count, "retry": False},
    )

    # Only retry if extremely short and on cloud, to prevent local timeout
    if word_count < 200 and provider_used != "ollama":
        logger.warning(
            f"Essay word count {word_count} out of range, retrying",
            extra={"word_count_check": "retry=true"},
        )
        retry_messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": "Please expand the essay with more detailed sections and examples to reach ~1,250 words.",
            },
        ]
        content, provider_used, model_used = await llm.complete(retry_messages, timeout=180)
        word_count = _count_words(content)

    # Build citations from referenced chunks
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

    return content, citations, provider_used, model_used, word_count
