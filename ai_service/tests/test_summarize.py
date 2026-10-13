import json

import ai_service.summarize as summ
from ai_service.llm import LLMError

GOOD = {
    "summary": "This material explains how plants make food and how cells release energy. " * 2,
    "key_points": ["Plants make food from sunlight", "Mitochondria release energy", ""],
}
CHAPTERS = ["Chapter 1. Introduction", "Chapter 5.  System Testing"]


def fake(payload):
    def _fake(prompt, system=None, retries=None, timeout=None):
        return payload if isinstance(payload, str) else json.dumps(payload)

    return _fake


def test_whole_document_summary(big_doc, monkeypatch):
    monkeypatch.setattr(summ, "ask_llm", fake(GOOD))
    res = summ.summarize(big_doc)
    assert res["summary"].startswith("This material")
    assert res["key_points"] == ["Plants make food from sunlight", "Mitochondria release energy"]
    assert res["sources"] and "error" not in res


def test_chapter_summary_uses_only_that_chapter(big_doc, monkeypatch):
    seen = {}

    def spy(prompt, system=None, retries=None, timeout=None):
        seen["prompt"] = prompt
        return json.dumps(GOOD)

    monkeypatch.setattr(summ, "ask_llm", spy)
    res = summ.summarize(big_doc, "Chapter 1 Plants")
    assert "Photosynthesis" in seen["prompt"]
    assert "Mitochondria" not in seen["prompt"]
    assert all(s["chapter"] == "Chapter 1 Plants" for s in res["sources"])


def test_unknown_chapter(big_doc):
    assert summ.summarize(big_doc, "Chapter 9 Nope")["error"] == "chapter_not_found"


def test_unknown_document(fresh_store):
    res = summ.summarize(404)
    assert res["error"] == "no_content" and res["summary"] == ""


def test_llm_down(big_doc, monkeypatch):
    def down(*args, **kwargs):
        raise LLMError("all providers failed")

    monkeypatch.setattr(summ, "ask_llm", down)
    assert summ.summarize(big_doc)["error"] == "llm_unavailable"


def test_bad_output(big_doc, monkeypatch):
    monkeypatch.setattr(summ, "ask_llm", fake("no json here"))
    assert summ.summarize(big_doc)["error"] == "bad_llm_output"


def test_pick_covers_every_chapter():
    pool = [{"chapter": f"Chapter {c}", "text": "x"} for c in range(1, 6) for _ in range(10)]
    picked = summ._pick(pool, 8)
    assert len(picked) == 8
    assert {p["chapter"] for p in picked} == {f"Chapter {c}" for c in range(1, 6)}


def test_overview_questions_are_detected():
    for q in [
        "What is this document about?",
        "Give me a summary of this document",
        "Summarize the document",
        "What are the main points?",
        "Give me an overview",
    ]:
        assert summ.wants_overview(q, CHAPTERS) == (True, None), q


def test_chapter_overview():
    assert summ.wants_overview("Summarize chapter 5", CHAPTERS) == (True, CHAPTERS[1])
    assert summ.wants_overview("Summarize chapter 9", CHAPTERS) == (False, None)


def test_specific_questions_are_not_overviews():
    for q in [
        "What is ShieldNet?",
        "Summarize the conclusion of the project.",
        "What does the testing chapter cover?",
        "How was the system tested?",
    ]:
        assert summ.wants_overview(q, CHAPTERS) == (False, None), q