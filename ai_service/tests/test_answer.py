import json

import ai_service.answer as answer_module
from ai_service import settings
from ai_service.llm import LLMError
import ai_service.summarize as summ

def fake_llm(payload):
    def _fake(prompt, system=None, retries=1, timeout=None, **kwargs):
        return payload if isinstance(payload, str) else json.dumps(payload)

    return _fake


def test_found_answer_returns_cited_source(stored_doc, monkeypatch):
    monkeypatch.setattr(settings, "MIN_SCORE", 0.0)
    monkeypatch.setattr(
        answer_module,
        "ask_llm",
        fake_llm({"found": True, "answer": "Plants make food from sunlight.", "sources": [1]}),
    )
    res = answer_module.answer(stored_doc, "How do plants make food?")
    assert res["found"] is True
    assert len(res["sources"]) == 1
    assert res["sources"][0]["page"] >= 1


def test_llm_says_not_found(stored_doc, monkeypatch):
    monkeypatch.setattr(settings, "MIN_SCORE", 0.0)
    monkeypatch.setattr(
        answer_module, "ask_llm", fake_llm({"found": False, "answer": "", "sources": []})
    )
    res = answer_module.answer(stored_doc, "Who painted the Mona Lisa?")
    assert res["found"] is False
    assert res["sources"] == []


def test_low_score_never_calls_llm(stored_doc, monkeypatch):
    monkeypatch.setattr(settings, "MIN_SCORE", 0.99)

    def boom(*args, **kwargs):
        raise AssertionError("LLM should not be called")

    monkeypatch.setattr(answer_module, "ask_llm", boom)
    assert answer_module.answer(stored_doc, "How do I bake a cake?")["found"] is False


def test_bad_citations_fall_back_to_top_hits(stored_doc, monkeypatch):
    monkeypatch.setattr(settings, "MIN_SCORE", 0.0)
    monkeypatch.setattr(
        answer_module, "ask_llm", fake_llm({"found": True, "answer": "Yes.", "sources": [99]})
    )
    assert len(answer_module.answer(stored_doc, "plants")["sources"]) >= 1


def test_llm_down(stored_doc, monkeypatch):
    monkeypatch.setattr(settings, "MIN_SCORE", 0.0)

    def down(*args, **kwargs):
        raise LLMError("all providers failed")

    monkeypatch.setattr(answer_module, "ask_llm", down)
    assert answer_module.answer(stored_doc, "plants")["error"] == "llm_unavailable"


def test_unparseable_output(stored_doc, monkeypatch):
    monkeypatch.setattr(settings, "MIN_SCORE", 0.0)
    monkeypatch.setattr(answer_module, "ask_llm", fake_llm("sorry, no json here"))
    assert answer_module.answer(stored_doc, "plants")["error"] == "bad_llm_output"


def test_parse_answer_variants():
    fenced = '```json\n{"found": true, "answer": "x", "sources": [1]}\n```'
    assert answer_module.parse_answer(fenced)["found"] is True
    assert answer_module.parse_answer('{"found": "false"}')["found"] is False
    assert answer_module.parse_answer("not json") is None


def test_overview_question_routes_to_summary(big_doc, monkeypatch):
    payload = {
        "summary": "This material explains how plants make food and how cells release energy. " * 2,
        "key_points": ["Plants make food", "Cells release energy"],
    }
    monkeypatch.setattr(summ, "ask_llm", fake_llm(payload))

    def boom(*args, **kwargs):
        raise AssertionError("the normal question path must not run")

    monkeypatch.setattr(answer_module, "retrieve", boom)
    res = answer_module.answer(big_doc, "What is this document about?")
    assert res["found"] is True and res["mode"] == "summary"
    assert "Key points" in res["answer"] and res["sources"]


def test_overview_with_llm_down(big_doc, monkeypatch):
    def down(*args, **kwargs):
        raise LLMError("all providers failed")

    monkeypatch.setattr(summ, "ask_llm", down)
    res = answer_module.answer(big_doc, "Give me a summary of this document")
    assert res["found"] is False and res["error"] == "llm_unavailable"