"""Tests: artifact HTML sanitization (security-critical)."""
from __future__ import annotations

import pytest

from app.services.artifact import sanitize_html


# ── Malicious payload tests ────────────────────────────────────────────────

@pytest.mark.parametrize("malicious_input,should_not_contain", [
    # Script tag XSS
    ("<p>Hello</p><script>alert('xss')</script>", "<script"),
    # Inline event handlers
    ('<img src="x" onerror="alert(1)">', "onerror"),
    ('<div onclick="alert(1)">click me</div>', "onclick"),
    ('<input onfocus="alert(1)">', "onfocus"),
    # javascript: URLs
    ('<a href="javascript:alert(1)">click</a>', "javascript:"),
    ('<a href="JAVASCRIPT:alert(1)">click</a>', "javascript:"),  # case-insensitive
    # External resources
    ('<img src="https://evil.com/track.png">', "evil.com"),
    ('<link rel="stylesheet" href="https://attacker.com/evil.css">', "attacker.com"),
    # Object / embed / form
    ('<object data="evil.swf"></object>', "<object"),
    ('<embed src="evil.swf">', "<embed"),
    # Script in event attribute on different elements
    ('<svg onload="alert(1)">', "onload"),
    ('<body onload="alert(1)">', "onload"),
])
def test_sanitize_strips_payload(malicious_input: str, should_not_contain: str):
    result = sanitize_html(malicious_input)
    assert should_not_contain.lower() not in result.lower(), (
        f"Payload not stripped: {should_not_contain!r} found in sanitized output.\n"
        f"Input: {malicious_input}\nOutput: {result}"
    )


def test_sanitize_preserves_safe_html():
    """Safe HTML should survive sanitization."""
    safe_html = "<h1>Title</h1><p>Hello <strong>world</strong></p><ul><li>Item 1</li></ul>"
    result = sanitize_html(safe_html)
    assert "Hello" in result
    assert "<strong>" in result or "world" in result  # content preserved


def test_sanitize_injects_csp_meta():
    """CSP meta tag must be injected into all sanitized HTML."""
    result = sanitize_html("<html><head><title>Test</title></head><body><p>Hello</p></body></html>")
    assert "Content-Security-Policy" in result
    assert "default-src 'none'" in result


def test_sanitize_fragment_gets_csp():
    """Even HTML fragments get CSP meta prepended."""
    result = sanitize_html("<p>Hello world</p>")
    assert "Content-Security-Policy" in result


def test_sanitize_script_in_style():
    """expression() in style is not a real vector but shouldn't crash sanitizer."""
    result = sanitize_html('<style>p { background: url("javascript:alert(1)") }</style>')
    # Should not raise; may or may not strip style content
    assert result is not None


def test_sanitize_multiple_scripts():
    """Multiple script tags all stripped."""
    html = "<script>a()</script><p>safe</p><script>b()</script>"
    result = sanitize_html(html)
    assert "<script" not in result.lower()
    assert "safe" in result


def test_sanitize_nested_event_handlers():
    """Nested attributes with event handlers stripped."""
    html = '<div data-x="<script>alert(1)</script>"><span onerror="x">text</span></div>'
    result = sanitize_html(html)
    assert "onerror" not in result.lower()
