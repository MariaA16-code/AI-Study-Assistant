import json
import random

import pytest

import ai_service.generate as gen
from ai_service.llm import LLMError


def mcq(n, question):
    return {
        "passage": n,
        "question": question,
        "options": [f"right {n}", f"wrong a{n}", f"wrong b{n}", f"wrong c{n}"],
        "correct_index": 0,
        "explanation": f"Because of fact {n}.",
    }


Q1 = mcq(1, "How do leaves use sunlight for photosynthesis?")
Q2 = mcq(2, "Where do mitochondria release stored energy?")
Q3 = mcq(3, "What genetic instructions does the nucleus carry?")


def fake_llm(entries):
    def _fake(prompt, system=None, retries=1, timeout=None):
        return json.dumps({"questions": entries})

    return _fake


@pytest.fixture(autouse=True)
def no_validation(monkeypatch):
    # Validation has its own tests; here we test the orchestration only.
    monkeypatch.setattr(gen, "validate_item", lambda kind, item, text: None)


def test_mcq_generation_end_to_end(big_doc, monkeypatch):
    monkeypatch.setattr(gen, "ask_llm", fake_llm([Q1, Q2, Q3]))
    res = gen.generate(big_doc, "mcq", "medium", 3, rng=random.Random(1))
    assert len(res["questions"]) == 3
    assert res["requested"] == 3
    assert "error" not in res
    for q in res["questions"]:
        assert q["type"] == "mcq" and len(q["options"]) == 4
        assert q["options"][q["correct_index"]].startswith("right")  # survives shuffling
        assert q["source"]["page"] >= 1


def test_chapter_filter(big_doc, monkeypatch):
    monkeypatch.setattr(gen, "ask_llm", fake_llm([Q1, Q2]))
    res = gen.generate(big_doc, "mcq", "low", 2, chapter="Chapter 2 Cells", rng=random.Random(1))
    assert res["questions"]
    assert all(q["source"]["chapter"] == "Chapter 2 Cells" for q in res["questions"])


def test_unknown_chapter(big_doc):
    res = gen.generate(big_doc, "mcq", "low", 2, chapter="Chapter 9 Nothing")
    assert res["error"] == "chapter_not_found"
    assert res["questions"] == []


def test_document_without_content(fresh_store):
    assert gen.generate(404, "mcq", "low", 2)["error"] == "no_content"


def test_llm_down(big_doc, monkeypatch):
    def down(*args, **kwargs):
        raise LLMError("all providers failed")

    monkeypatch.setattr(gen, "ask_llm", down)
    res = gen.generate(big_doc, "mcq", "low", 2)
    assert res["error"] == "llm_unavailable"
    assert res["questions"] == []


def test_partial_results_add_a_warning(big_doc, monkeypatch):
    monkeypatch.setattr(gen, "ask_llm", fake_llm([Q1]))  # same question every time
    res = gen.generate(big_doc, "mcq", "low", 3, rng=random.Random(1))
    assert len(res["questions"]) == 1
    assert any("Only 1 of 3" in w for w in res["warnings"])
    assert res["rejected"]["duplicate question"] >= 1


def test_mixed_plan():
    assert gen._plan("mixed", 5) == {"mcq": 3, "short": 1, "long": 1}
    assert gen._plan("short", 4) == {"short": 4}


def test_usable_chunks():
    assert gen._usable("word " * 60)
    assert not gen._usable("short")
    assert not gen._usable("12345 " * 60)


def test_list_chapters(big_doc):
    assert gen.list_chapters(big_doc) == ["Chapter 1 Plants", "Chapter 2 Cells"]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        gen.generate(1, "essay", "low", 3)
    with pytest.raises(ValueError):
        gen.generate(1, "mcq", "extreme", 3)
    with pytest.raises(ValueError):
        gen.generate(1, "mcq", "low", 0)