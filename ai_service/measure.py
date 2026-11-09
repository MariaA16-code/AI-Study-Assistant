"""Measure upload, chat and generation times.
Usage (from repo root, venv active):
  python -m ai_service.measure "path/to/file.pdf" "a specific question"
  python -m ai_service.measure "path/to/file.pdf" "a specific question" --big
"""
import sys
import time

from ai_service import api

DOC_ID = 987654  # temporary test id, deleted at the end


def timed(label, fn):
    start = time.perf_counter()
    try:
        result = fn()
    except Exception as exc:
        print(f"[{label}] FAILED: {exc}")
        return None
    secs = time.perf_counter() - start
    print(f"[{label}] {secs:.1f} s")
    return result


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    path, question = sys.argv[1], sys.argv[2]
    big = "--big" in sys.argv

    try:
        res = timed("upload + processing", lambda: api.process_document(DOC_ID, path))
        if res:
            print("   ", {k: res.get(k) for k in ("status", "pages", "chunks")})

        a = timed("chat: specific question", lambda: api.answer_question(DOC_ID, question))
        if a:
            print("    found:", a.get("found"), "| sources:", len(a.get("sources", [])))

        a = timed("chat: vague question", lambda: api.answer_question(DOC_ID, "What is this document about?"))
        if a:
            print("    found:", a.get("found"), "| mode:", a.get("mode"))

        g = timed("generate: 5 MCQ (medium)", lambda: api.generate_questions(DOC_ID, "mcq", "medium", 5))
        if g:
            print("    got:", len(g.get("questions", [])), "of", g.get("requested"))

        if big:
            g = timed("generate: 20 mixed (medium)", lambda: api.generate_questions(DOC_ID, "mixed", "medium", 20))
            if g:
                print("    got:", len(g.get("questions", [])), "of", g.get("requested"))
    finally:
        api.delete_document(DOC_ID)
        print("test document deleted")


if __name__ == "__main__":
    main()