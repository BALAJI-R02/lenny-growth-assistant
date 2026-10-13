"""Message router: classifies each user message as QA, ESSAY, or ARTIFACT."""
from __future__ import annotations

import logging
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class Route(str, Enum):
    QA = "QA"
    ESSAY = "ESSAY"
    ARTIFACT = "ARTIFACT"
    CHITCHAT = "CHITCHAT"


# Keyword triggers — fast path (case-insensitive substring match)
_ESSAY_KEYWORDS = [
    "write a ship 30",
    "write ship 30",
    "ship 30 essay",
    "ship30 essay",
    "write an essay",
    "draft an essay",
    "write a 1250",
    "write a 1,250",
    "digital essay",
]

_ARTIFACT_KEYWORDS = [
    "generate artifact",
    "create html",
    "create markdown",
    "generate a markdown",
    "generate html",
    "make a document",
    "write html",
    "generate doc",
    "create a document",
    "generate a document",
    "produce html",
    "produce markdown",
    "build an html",
    "make html",
]

_CHITCHAT_KEYWORDS = [
    "hello",
    "hi",
    "hey",
    "howdy",
    "sup",
    "what's up",
    "whats up",
    "good morning",
    "good afternoon",
    "good evening",
    "thanks",
    "thank you",
    "ty",
    "thx",
    "cheers",
    "bye",
    "goodbye",
    "see you",
    "who are you",
    "what are you",
    "what can you do",
    "help me",
    "how are you",
]


def classify(message: str) -> Route:
    """
    Classify a message into QA, ESSAY, ARTIFACT, or CHITCHAT.

    Rules (in order of priority):
    1. Essay keywords → ESSAY
    2. Artifact keywords → ARTIFACT
    3. Chitchat / greeting keywords → CHITCHAT
    4. Default → QA

    LLM fallback is available when ROUTER_USE_LLM=true but is a no-op here
    because the keyword rules are sufficient for MVP and keep costs/latency low.
    """
    lower = message.lower().strip()

    for keyword in _ESSAY_KEYWORDS:
        if keyword in lower:
            logger.debug(f"Classified as ESSAY via keyword: {keyword!r}")
            return Route.ESSAY

    for keyword in _ARTIFACT_KEYWORDS:
        if keyword in lower:
            logger.debug(f"Classified as ARTIFACT via keyword: {keyword!r}")
            return Route.ARTIFACT

    # Exact match or starts-with for short greetings
    for keyword in _CHITCHAT_KEYWORDS:
        if lower == keyword or lower.startswith(keyword):
            logger.debug(f"Classified as CHITCHAT via keyword: {keyword!r}")
            return Route.CHITCHAT

    logger.debug("Classified as QA (default)")
    return Route.QA
