"""Query rewriter: converts follow-up questions into standalone search queries."""
from __future__ import annotations

import logging

from app.services import llm

logger = logging.getLogger(__name__)

_REWRITE_SYSTEM = """\
You are a search query optimizer. Your job is to rewrite a follow-up question \
into a self-contained search query that captures the user's intent without \
needing the conversation history.

Rules:
- Output ONLY the rewritten query, no explanation
- Keep it concise (5-15 words)
- Preserve the key topic and specificity
- If the message is already standalone, return it unchanged
"""


async def rewrite(
    message: str,
    history: list[dict],
) -> str:
    """
    Rewrite a follow-up question into a standalone search query.

    If history is empty or message appears standalone, returns message unchanged.
    """
    if not history:
        return message

    # Simple heuristics: if message starts with "what about", "and", "also", etc.
    followup_markers = [
        "what about",
        "and ",
        "also ",
        "how about",
        "tell me more",
        "what else",
        "can you elaborate",
        "more about",
        "specifically",
    ]
    lower = message.lower()
    is_followup = any(lower.startswith(m) for m in followup_markers) or len(message.split()) < 5

    if not is_followup:
        return message

    # Build context from recent history (last 3 turns)
    recent = history[-6:]  # 3 pairs max
    context_lines = []
    for h in recent:
        role = h.get("role", "user")
        content = h.get("content", "")[:200]  # truncate long messages
        context_lines.append(f"{role.upper()}: {content}")

    context = "\n".join(context_lines)
    prompt = f"""Previous conversation:
{context}

Follow-up question: {message}

Rewrite as a standalone search query:"""

    try:
        rewritten, _, _ = await llm.complete(
            [
                {"role": "system", "content": _REWRITE_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            timeout=30,
        )
        rewritten = rewritten.strip().strip('"').strip("'")
        logger.info(f"Query rewrite: {message!r} -> {rewritten!r}")
        return rewritten
    except Exception as e:
        logger.warning(f"Query rewrite failed, using original: {e}")
        return message
