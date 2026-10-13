"""LLM provider abstraction layer.

Supports: ollama, anthropic, openai.
Automatic fallback: if primary provider fails and a cloud key exists, switch.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Error codes
LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
LLM_TIMEOUT = "LLM_TIMEOUT"


class LLMUnavailableError(RuntimeError):
    def __init__(self, message: str, code: str = LLM_UNAVAILABLE):
        super().__init__(message)
        self.code = code


async def _call_ollama(messages: list[dict], model: str, timeout: int) -> str:
    """Call Ollama chat completions API."""
    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]


async def _call_anthropic(messages: list[dict], model: str, timeout: int) -> str:
    """Call Anthropic Messages API."""
    import anthropic  # lazy import

    client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        timeout=timeout,
    )
    # Separate system messages from conversation
    system_content = ""
    chat_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_content += msg["content"] + "\n"
        else:
            chat_messages.append({"role": msg["role"], "content": msg["content"]})

    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_content.strip() or "You are a helpful assistant.",
        messages=chat_messages,
    )
    return response.content[0].text


async def _call_openai(messages: list[dict], model: str, timeout: int) -> str:
    """Call OpenAI Chat Completions API."""
    from openai import AsyncOpenAI  # lazy import

    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=timeout)
    response = await client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        max_tokens=4096,
        temperature=0.1,
    )
    return response.choices[0].message.content or ""


async def complete(
    messages: list[dict[str, Any]],
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout: int | None = None,
) -> tuple[str, str, str]:
    """
    Call the configured LLM provider.

    Returns: (content, provider_used, model_used)
    Raises: LLMUnavailableError if all providers fail.
    """
    provider = provider or settings.llm_provider
    model = model or settings.model_name
    timeout = timeout or settings.llm_timeout_seconds

    providers_to_try: list[tuple[str, str]] = [(provider, model)]

    # Add fallback if primary is ollama and cloud keys exist
    if provider == "ollama" and settings.has_cloud_fallback:
        fallback_p = settings.fallback_provider
        fallback_model = (
            "claude-3-haiku-20240307"
            if fallback_p == "anthropic"
            else "gpt-4o-mini"
        )
        providers_to_try.append((fallback_p, fallback_model))  # type: ignore[arg-type]

    last_error: Exception | None = None
    used_fallback = False

    for p, m in providers_to_try:
        try:
            if p == "ollama":
                content = await _call_ollama(messages, m, timeout)
            elif p == "anthropic":
                content = await _call_anthropic(messages, m, timeout)
            elif p == "openai":
                content = await _call_openai(messages, m, timeout)
            else:
                raise LLMUnavailableError(f"Unknown provider: {p}")

            if used_fallback:
                logger.warning(
                    "Using fallback provider",
                    extra={"primary_provider": provider, "fallback_provider": p},
                )
            return content, p, m

        except httpx.ConnectError as e:
            logger.warning(f"Provider {p} unreachable: {e}")
            last_error = e
            used_fallback = True
        except httpx.TimeoutException as e:
            logger.warning(f"Provider {p} timed out: {e}")
            last_error = LLMUnavailableError(
                f"Request to {p} timed out after {timeout}s", LLM_TIMEOUT
            )
            used_fallback = True
        except Exception as e:
            logger.error(f"Provider {p} error: {e}")
            last_error = e
            used_fallback = True

    msg = "Ollama is unreachable and no cloud fallback is configured."
    if settings.has_cloud_fallback:
        msg = f"All LLM providers failed. Last error: {last_error}"
    raise LLMUnavailableError(msg)


async def check_health() -> tuple[bool, str]:
    """Check if the primary LLM provider is reachable. Returns (ok, detail)."""
    try:
        if settings.llm_provider == "ollama":
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.ollama_base_url}/api/tags")
                resp.raise_for_status()
                return True, "ok"
        elif settings.llm_provider == "anthropic":
            if not settings.anthropic_api_key:
                return False, "ANTHROPIC_API_KEY not set"
            return True, "ok"
        elif settings.llm_provider == "openai":
            if not settings.openai_api_key:
                return False, "OPENAI_API_KEY not set"
            return True, "ok"
    except Exception as e:
        return False, str(e)
    return False, "unknown"
