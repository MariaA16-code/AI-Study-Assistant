import inspect
import subprocess
import sys
from pathlib import Path

import ai_service
from ai_service import api

ROOT = Path(__file__).resolve().parents[2]  # the repo root


def test_public_functions_exist():
    assert set(ai_service.__all__) == {
        "process_document",
        "answer_question",
        "generate_questions",
        "list_chapters",
        "delete_document",
        "summarize_document",
    }


def test_signatures_are_stable():
    def params(fn):
        return list(inspect.signature(fn).parameters)

    assert params(api.process_document) == ["document_id", "file_path"]
    assert params(api.answer_question) == ["document_id", "question"]
    assert params(api.generate_questions) == [
        "document_id", "question_type", "difficulty", "count", "chapter",
    ]
    assert params(api.list_chapters) == ["document_id"]
    assert params(api.delete_document) == ["document_id"]
    assert params(api.summarize_document) == ["document_id", "chapter"]


def test_result_shapes_for_an_unknown_document(fresh_store):
    ans = api.answer_question(404, "anything")
    assert set(ans) >= {"answer", "found", "sources"} and ans["found"] is False

    gen = api.generate_questions(404, "mcq", "low", 3)
    assert set(gen) >= {"questions", "requested", "warnings", "error"}
    assert gen["questions"] == [] and gen["error"] == "no_content"

    assert api.list_chapters(404) == []


def test_process_failure_shape(fresh_store, tmp_path):
    res = api.process_document(1, str(tmp_path / "missing.pdf"))
    assert set(res) == {"status", "pages", "chunks", "warnings"}
    assert res["status"] == "failed"


def test_import_does_not_load_heavy_libraries():
    # The backend teammate must be able to import ai_service before the AI
    # libraries are installed. Heavy imports must stay inside the functions.
    code = (
        "import sys, ai_service; "
        "heavy = {'chromadb', 'fastembed', 'pdfplumber', 'docx', "
        "'google.genai', 'groq', 'rank_bm25'}; "
        "print(sorted(heavy & set(sys.modules)))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True
    )
    assert out.stdout.strip() == "[]", out.stderr

def test_summarize_shape_for_an_unknown_document(fresh_store):
       res = api.summarize_document(404)
       assert set(res) >= {"summary", "key_points", "chapter", "sources", "error"}
       assert res["summary"] == "" and res["error"] == "no_content"