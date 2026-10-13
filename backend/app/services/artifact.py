"""Artifact generation + server-side HTML sanitization."""
from __future__ import annotations

import logging
import re

import bleach

from app.services import llm
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

# ── Bleach allowlist ───────────────────────────────────────────────────────

_ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "strong", "b", "em", "i", "u", "s", "code", "pre",
    "ul", "ol", "li",
    "blockquote",
    "a",
    "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "div", "span",
    "section", "article", "header", "footer", "main",
    "style",
    "meta",
    "html", "head", "body",
    "title",
]

_ALLOWED_ATTRS: dict[str, list[str]] = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
    "div": ["class", "id", "style"],
    "span": ["class", "id", "style"],
    "p": ["class", "style"],
    "h1": ["class"], "h2": ["class"], "h3": ["class"],
    "table": ["class", "style"],
    "section": ["class", "id"],
    "meta": ["http-equiv", "content", "name"],
    "style": [],
    "code": ["class"],
    "pre": ["class"],
}

_CSP_META = (
    '<meta http-equiv="Content-Security-Policy" '
    'content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:;">'
)

# Patterns that must be stripped even if bleach misses them
_DANGEROUS_PATTERNS = [
    re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"\bon\w+\s*=", re.IGNORECASE),  # onerror=, onclick=, etc.
    re.compile(r"<iframe(?!.*srcdoc)", re.IGNORECASE),  # iframes without srcdoc
    re.compile(r"<object[\s\S]*?</object>", re.IGNORECASE),
    re.compile(r"<embed[^>]*>", re.IGNORECASE),
    re.compile(r"<form[\s\S]*?</form>", re.IGNORECASE),
    re.compile(r'src\s*=\s*["\']https?://', re.IGNORECASE),  # external src
    re.compile(r'href\s*=\s*["\']https?://', re.IGNORECASE),  # external href
]


def sanitize_html(raw_html: str) -> str:
    """
    Server-side HTML sanitization pipeline:
    1. Strip dangerous patterns with regex
    2. Clean with bleach allowlist
    3. Inject CSP meta tag
    4. Wrap in sandboxed iframe (done in API layer, not here)
    """
    content = raw_html

    # Step 1: Strip dangerous patterns
    for pattern in _DANGEROUS_PATTERNS:
        content = pattern.sub("", content)

    # Step 2: Bleach clean
    content = bleach.clean(
        content,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
        strip_comments=True,
    )

    # Step 3: Inject CSP meta if it's a full HTML document
    if "<head>" in content.lower():
        content = content.replace("<head>", f"<head>\n{_CSP_META}", 1)
    elif "<html" in content.lower():
        content = _CSP_META + "\n" + content
    else:
        # Fragment — prepend CSP meta
        content = _CSP_META + "\n" + content

    return content


# ── Generation ─────────────────────────────────────────────────────────────

_ARTIFACT_SYSTEM = """\
You are an expert technical writer. Generate clean, well-structured content based on the user's request.

For HTML artifacts:
- Write complete, self-contained HTML with inline CSS (no external resources)
- Use clean, modern design with tasteful styling
- Do NOT include <script> tags or JavaScript
- Do NOT reference external URLs in src or href attributes
- Use only data: URIs for images if needed

For Markdown artifacts:
- Use proper GFM (GitHub Flavored Markdown)
- Include tables, code blocks, and headings as appropriate
- Do not include raw HTML blocks

Return ONLY the artifact content, no preamble or explanation.
"""


async def generate(
    request: str,
    artifact_type: str,
    chunks: list[RetrievedChunk] | None = None,
    conversation_context: str = "",
) -> tuple[str, str, str, str]:
    """
    Generate an artifact (markdown or html) from the request.

    Returns: (raw_content, sanitized_content, provider, model)
    - For HTML: sanitized_content has script/exfil stripped + CSP injected
    - For Markdown: raw and sanitized are the same (client handles DOMPurify)
    """
    context_parts = []
    if conversation_context:
        context_parts.append(f"Conversation context:\n{conversation_context}")
    if chunks:
        evidence = "\n\n".join(
            f"[{i}] {c.episode} — {c.guest}: {c.text[:300]}"
            for i, c in enumerate(chunks, 1)
        )
        context_parts.append(f"Available evidence from transcripts:\n{evidence}")

    full_request = "\n\n".join(context_parts + [f"Request: {request}"])

    type_instruction = (
        "Generate a complete, self-contained HTML document with inline CSS."
        if artifact_type == "html"
        else "Generate a well-structured Markdown document."
    )

    messages = [
        {"role": "system", "content": _ARTIFACT_SYSTEM},
        {"role": "user", "content": f"{type_instruction}\n\n{full_request}"},
    ]

    raw_content, provider_used, model_used = await llm.complete(messages, timeout=300)

    if artifact_type == "html":
        sanitized = sanitize_html(raw_content)
    else:
        sanitized = raw_content  # Markdown sanitized client-side with DOMPurify

    return raw_content, sanitized, provider_used, model_used


def infer_type(request: str) -> str:
    """Infer artifact type from request text."""
    lower = request.lower()
    html_hints = ["html", "webpage", "web page", "landing page", "styled"]
    if any(h in lower for h in html_hints):
        return "html"
    return "markdown"


def infer_title(request: str, artifact_type: str) -> str:
    """Generate a short title from the request."""
    # Take first 60 chars of request, clean up
    title = request[:60].strip().rstrip(".,!?")
    prefix = "HTML: " if artifact_type == "html" else "Doc: "
    return prefix + title
