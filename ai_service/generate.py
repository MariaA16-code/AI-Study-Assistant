"""generate_questions: pick passages, ask the LLM, validate, return clean questions."""
import logging
import math
import random
from collections import Counter

from . import settings
from .llm import LLMError, ask_llm
from .prompts import SYSTEM_GENERATE, build_generate_prompt
from .retrieve import tokenize
from .store import get_all_chunks
from .util import extract_json
from .validate import validate_item

logger = logging.getLogger(__name__)

TYPES = {"mcq", "short", "long", "mixed"}
DIFFICULTIES = {"low", "medium", "high"}
BATCH = 5
MIXED_PATTERN = ["mcq", "mcq", "short", "mcq", "long"]


def list_chapters(document_id: int) -> list[str]:
    seen: list[str] = []
    for c in get_all_chunks(document_id):
        if c["chapter"] and c["chapter"] not in seen:
            seen.append(c["chapter"])
    return seen


def _usable(text: str) -> bool:
    """Skip tiny chunks, number-heavy tables and reference lists."""
    letters = sum(ch.isalpha() for ch in text)
    visible = sum(not ch.isspace() for ch in text)
    return (
        len(text) >= 200
        and visible > 0
        and letters / visible >= 0.65
        and text.lower().count("http") < 2
    )


def _select_pool(chunks: list[dict], chapter: str | None) -> tuple[list[dict], str | None]:
    if chapter:
        wanted = chapter.lower()
        chunks = [
            c for c in chunks
            if c["chapter"] and (c["chapter"].lower() == wanted or wanted in c["chapter"].lower())
        ]
        if not chunks:
            return [], "chapter_not_found"
    elif any(c["chapter"] for c in chunks):
        chunks = [c for c in chunks if c["chapter"]]  # skip title pages and front matter
    pool = [c for c in chunks if _usable(c["text"])]
    return pool, (None if pool else "no_content")


def _plan(question_type: str, count: int) -> dict[str, int]:
    if question_type != "mixed":
        return {question_type: count}
    plan: dict[str, int] = {}
    for i in range(count):
        kind = MIXED_PATTERN[i % len(MIXED_PATTERN)]
        plan[kind] = plan.get(kind, 0) + 1
    return plan


def _spread(pool: list[dict], k: int, rng: random.Random) -> list[dict]:
    """k passages spread evenly over the pool, from a random starting point."""
    n = len(pool)
    if n <= k:
        picked = list(pool)
        rng.shuffle(picked)
        return picked
    offset = rng.randrange(n)
    return [pool[(offset + (i * n) // k) % n] for i in range(k)]


def _similar(a: set[str], b: set[str]) -> bool:
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= 0.8


def _build_item(kind: str, raw: dict, hit: dict, difficulty: str) -> dict:
    item = {
        "type": kind,
        "question": raw["question"].strip(),
        "difficulty": difficulty,
        "source": {
            "chapter": hit["chapter"],
            "page": hit["page_start"],
            "page_end": hit["page_end"],
            "snippet": hit["text"][:300],
        },
    }
    if kind == "mcq":
        idx = raw["correct_index"]
        if isinstance(idx, str):
            idx = int(idx.strip())
        item["options"] = [o.strip() for o in raw["options"]]
        item["correct_index"] = idx
        item["explanation"] = raw["explanation"].strip()
    else:
        item["model_answer"] = raw["model_answer"].strip()
    return item


def _shuffle_options(item: dict, rng: random.Random) -> None:
    """Models like putting the right answer first, so shuffle the options."""
    correct = item["options"][item["correct_index"]]
    rng.shuffle(item["options"])
    item["correct_index"] = item["options"].index(correct)


def _generate_kind(
    kind: str,
    difficulty: str,
    n: int,
    pool: list[dict],
    rng: random.Random,
    seen_tokens: list[set[str]],
    rejected: list[str],
) -> tuple[list[dict], str | None]:
    items: list[dict] = []
    for _ in range(math.ceil(n / BATCH) + 2):
        remaining = n - len(items)
        if remaining <= 0:
            break
        want = min(BATCH, remaining + 1)  # one extra absorbs a rejected question
        passages = _spread(pool, want, rng)
        prompt = build_generate_prompt(kind, difficulty, passages, want)
        try:
            raw = ask_llm(prompt, system=SYSTEM_GENERATE, retries=0, timeout=settings.GEN_TIMEOUT)
        except LLMError as exc:
            logger.warning("LLM unavailable during generation: %s", exc)
            return items, "llm_unavailable"

        data = extract_json(raw)
        entries = data.get("questions") if data else None
        if not isinstance(entries, list):
            rejected.append("unparseable reply")
            continue

        for entry in entries:
            if len(items) >= n:
                break
            if not isinstance(entry, dict):
                continue
            try:
                number = int(entry.get("passage"))
            except (TypeError, ValueError):
                rejected.append("missing passage number")
                continue
            if not 1 <= number <= len(passages):
                rejected.append("bad passage number")
                continue
            hit = passages[number - 1]
            reason = validate_item(kind, entry, hit["text"])
            if reason:
                rejected.append(reason)
                continue
            tokens = set(tokenize(entry["question"]))
            if any(_similar(tokens, seen) for seen in seen_tokens):
                rejected.append("duplicate question")
                continue
            item = _build_item(kind, entry, hit, difficulty)
            if kind == "mcq":
                _shuffle_options(item, rng)
            seen_tokens.append(tokens)
            items.append(item)
    return items, None


def generate(
    document_id: int,
    question_type: str,
    difficulty: str,
    count: int,
    chapter: str | None = None,
    rng: random.Random | None = None,
) -> dict:
    rng = rng or random.Random()
    question_type = (question_type or "").strip().lower()
    difficulty = (difficulty or "").strip().lower()
    chapter = (chapter or "").strip() or None
    if question_type not in TYPES:
        raise ValueError(f"question_type must be one of {sorted(TYPES)}")
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {sorted(DIFFICULTIES)}")
    try:
        count = int(count)
    except (TypeError, ValueError):
        raise ValueError("count must be a whole number") from None
    if count < 1:
        raise ValueError("count must be at least 1")

    warnings: list[str] = []
    if count > settings.MAX_QUESTIONS:
        count = settings.MAX_QUESTIONS
        warnings.append(f"Limited to {count} questions per request.")

    result: dict = {"questions": [], "requested": count, "warnings": warnings}
    chunks = get_all_chunks(document_id)
    pool, error = _select_pool(chunks, chapter) if chunks else ([], "no_content")
    if error:
        result["error"] = error
        return result

    questions: list[dict] = []
    seen_tokens: list[set[str]] = []
    rejected: list[str] = []
    llm_error = None
    for kind, n in _plan(question_type, count).items():
        items, err = _generate_kind(kind, difficulty, n, pool, rng, seen_tokens, rejected)
        questions.extend(items)
        if err:
            llm_error = err
            break

    result["questions"] = questions
    result["rejected"] = dict(Counter(rejected))  # debug info; the backend can ignore it
    if llm_error and not questions:
        result["error"] = llm_error
    elif llm_error:
        warnings.append("The AI service stopped early, so fewer questions were generated.")
    if len(questions) < count and "error" not in result:
        warnings.append(f"Only {len(questions)} of {count} questions passed quality checks.")
    return result