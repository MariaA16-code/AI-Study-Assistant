import pytest

from ai_service import llm, settings
from ai_service.llm import LLMError


@pytest.fixture(autouse=True)
def fast_and_gemini_first(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "LLM_RETRY_DELAY", 0.0)


def provider(calls, name, outcomes):
    outcomes = list(outcomes)

    def call(prompt, system, timeout):
        calls.append(name)
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return call


def install(monkeypatch, gemini, groq):
    calls: list[str] = []
    monkeypatch.setattr(
        llm,
        "_PROVIDERS",
        {"gemini": provider(calls, "gemini", gemini), "groq": provider(calls, "groq", groq)},
    )
    return calls


def test_retries_a_503_then_succeeds(monkeypatch):
    calls = install(monkeypatch, [Exception("503 UNAVAILABLE"), "ok"], ["groq"])
    assert llm.ask_llm("hi", retries=1) == "ok"
    assert calls == ["gemini", "gemini"]


def test_no_retries_falls_back_at_once(monkeypatch):
    calls = install(monkeypatch, [Exception("503 UNAVAILABLE")], ["from groq"])
    assert llm.ask_llm("hi", retries=0) == "from groq"
    assert calls == ["gemini", "groq"]


def test_retries_exhausted_then_fallback(monkeypatch):
    calls = install(
        monkeypatch, [Exception("503"), Exception("504 timeout")], ["from groq"]
    )
    assert llm.ask_llm("hi", retries=1) == "from groq"
    assert calls == ["gemini", "gemini", "groq"]


def test_bad_key_is_never_retried(monkeypatch):
    calls = install(
        monkeypatch, [Exception("400 INVALID_ARGUMENT API key not valid")], ["from groq"]
    )
    assert llm.ask_llm("hi", retries=3) == "from groq"
    assert calls == ["gemini", "groq"]


def test_default_retries_come_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "LLM_RETRIES", 2)
    calls = install(
        monkeypatch, [Exception("503"), Exception("503"), "ok"], ["groq"]
    )
    assert llm.ask_llm("hi") == "ok"
    assert calls == ["gemini", "gemini", "gemini"]


def test_all_providers_failing_raises(monkeypatch):
    install(monkeypatch, [Exception("401 bad key")], [Exception("401 bad key")])
    with pytest.raises(LLMError):
        llm.ask_llm("hi", retries=0)