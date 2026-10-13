"""One entry point for the whole project: ask_llm(prompt) -> str.

LLM_PROVIDER from .env is tried first. If it fails (timeout, rate limit,
retired model), the other provider is tried automatically.
"""
import logging
import time

from . import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when every provider failed."""


def _call_gemini(prompt: str, system: str | None, timeout: int) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=timeout * 1000),
    )
    cfg = types.GenerateContentConfig(system_instruction=system) if system else None
    resp = client.models.generate_content(
        model=settings.GEMINI_MODEL, contents=prompt, config=cfg
    )
    return resp.text or ""


def _call_groq(prompt: str, system: str | None, timeout: int) -> str:
    from groq import Groq

    client = Groq(
        api_key=settings.GROQ_API_KEY,
        timeout=float(timeout),
        max_retries=0,
    )
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=settings.GROQ_MODEL, messages=messages
    )
    return resp.choices[0].message.content or ""


_PROVIDERS = {"gemini": _call_gemini, "groq": _call_groq}


def _is_retryable(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        w in text
        for w in ("timeout", "timed out", "unavailable", "overloaded",
                  "502", "503", "504", "empty reply")
    )


def ask_llm(
    prompt: str,
    system: str | None = None,
    retries: int | None = None,
    timeout: int | None = None,
) -> str:
    retries = settings.LLM_RETRIES if retries is None else retries
    timeout = timeout or settings.LLM_TIMEOUT
    primary = settings.LLM_PROVIDER.lower()
    if primary not in _PROVIDERS:
        raise LLMError(f"Unknown LLM_PROVIDER '{primary}'. Use 'gemini' or 'groq'.")
    order = [primary] + [p for p in _PROVIDERS if p != primary]

    errors = []
    for name in order:
        for attempt in range(retries + 1):
            try:
                text = _PROVIDERS[name](prompt, system, timeout)
                if text.strip():
                    return text
                raise ValueError("empty reply")
            except Exception as exc:
                msg = f"{name} (try {attempt + 1}): {str(exc)[:150]}"
                errors.append(msg)
                logger.warning(msg)
                if not _is_retryable(exc):
                    break  # bad key, retired model, rate limit: next provider now
                if attempt < retries:
                    time.sleep(settings.LLM_RETRY_DELAY * (attempt + 1))
    raise LLMError("All providers failed: " + " | ".join(errors))