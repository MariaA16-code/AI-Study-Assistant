"""Shows why long questions are rejected: the length and grounded share of each model answer.

Run from the repo root with the venv active and the backend stopped:
    python -m ai_service.try_long
"""
import random

from . import settings
from .generate import _select_pool, _spread
from .llm import ask_llm
from .prompts import SYSTEM_GENERATE, build_generate_prompt
from .retrieve import tokenize
from .store import get_all_chunks
from .util import extract_json
from .validate import _grounded_ratio, validate_item

DOC_ID = 5        # the document id shown by GET /api/documents/
CHAPTER = None    # for example "Chapter 1", or None for all chapters
N = 5             # how many long questions to ask for

pool, error = _select_pool(get_all_chunks(DOC_ID), CHAPTER)
if error:
    raise SystemExit(f"Problem with the document: {error}")

passages = _spread(pool, N, random.Random())
raw = ask_llm(
    build_generate_prompt("long", "medium", passages, N),
    system=SYSTEM_GENERATE,
    timeout=settings.GEN_TIMEOUT,
)
data = extract_json(raw)
if data is None:
    print("The reply could not be read as JSON. This is the start of the reply:\n")
    print(raw[:600])
    raise SystemExit
questions = data.get("questions", [])
print(f"The model returned {len(questions)} question(s)\n")

for i, entry in enumerate(questions, start=1):
    answer = str(entry.get("model_answer", "")).strip()
    try:
        passage = passages[int(entry.get("passage")) - 1]["text"]
    except (TypeError, ValueError, IndexError):
        print(f"{i}. bad passage number: {entry.get('passage')!r}\n")
        continue
    ratio = _grounded_ratio(answer, set(tokenize(passage)))
    reason = validate_item("long", entry, passage)
    print(f"{i}. answer length = {len(answer)} chars (allowed 100 to 2500)")
    print(f"   grounded share = {ratio:.2f} (must be at least 0.40)")
    print(f"   result: {reason or 'ACCEPTED'}\n")