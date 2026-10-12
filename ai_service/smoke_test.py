"""End-to-end check of the public contract.

Usage (from the repo root, venv active):
    python -m ai_service.smoke_test "path\\to\\file.pdf" "a question the file answers"
"""
import sys
import time

from . import (
    answer_question,
    delete_document,
    generate_questions,
    list_chapters,
    process_document,
)

DOC_ID = 9999

if len(sys.argv) < 2:
    sys.exit('usage: python -m ai_service.smoke_test "path\\to\\file" "a question"')
path = sys.argv[1]
question = " ".join(sys.argv[2:]) or "What is this document about?"


def step(title: str) -> None:
    print(f"\n=== {title}")


step("process_document")
start = time.time()
res = process_document(DOC_ID, path)
print(res, f"({round(time.time() - start, 1)} s)")
if res["status"] != "ready":
    sys.exit("processing failed, stopping here")

step("list_chapters")
chapters = list_chapters(DOC_ID)
print(chapters)

step("answer_question (answer is in the file)")
ans = answer_question(DOC_ID, question)
print("found:", ans["found"], "|", ans["answer"][:300])
print("sources:", [(s["chapter"], s["page"]) for s in ans["sources"]])

step("answer_question (answer is NOT in the file)")
off = answer_question(DOC_ID, "How do I bake a chocolate cake?")
print("found:", off["found"])

step("generate_questions (mixed, medium, 5)")
gen = generate_questions(DOC_ID, "mixed", "medium", 5, chapters[0] if chapters else None)
print(
    len(gen["questions"]), "of", gen["requested"],
    "| warnings:", gen["warnings"], "| error:", gen.get("error"),
)
for q in gen["questions"]:
    print("-", q["type"], "|", q["question"][:100])

step("delete_document")
delete_document(DOC_ID)
print("deleted")