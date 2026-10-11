"""Quality checks for generated questions. Pure functions: no LLM, no network."""
import re

from .retrieve import tokenize

BANNED_IN_QUESTION = re.compile(
    r"\b(passage|excerpt)\b|\bthe (given |above )?text\b", re.IGNORECASE
)
BANNED_OPTION = re.compile(
    r"\b(all|none) of the above\b|\bboth [a-d] and [a-d]\b", re.IGNORECASE
)


def _clean(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _grounded_ratio(text: str, vocab: set[str]) -> float:
    """Share of the text's content words that appear in the source passage."""
    tokens = tokenize(text)
    if not tokens:
        return 1.0  # nothing to judge
    return sum(t in vocab for t in tokens) / len(tokens)


def validate_item(kind: str, item: dict, passage_text: str) -> str | None:
    """Return None when the question is good, otherwise a short reason."""
    question = _clean(item.get("question"))
    if not 10 <= len(question) <= 400:
        return "question length"
    if BANNED_IN_QUESTION.search(question):
        return "mentions the passage"
    vocab = set(tokenize(passage_text))
    if kind == "mcq":
        return _validate_mcq(item, vocab)
    if kind in ("short", "long"):
        return _validate_written(kind, item, vocab)
    return "unknown type"


def _validate_mcq(item: dict, vocab: set[str]) -> str | None:
    options = item.get("options")
    if not isinstance(options, list) or len(options) != 4:
        return "needs exactly 4 options"
    options = [_clean(o) for o in options]
    if any(not o or len(o) > 200 for o in options):
        return "empty or too long option"
    if len({o.lower() for o in options}) != 4:
        return "duplicate options"
    if any(BANNED_OPTION.search(o) for o in options):
        return "all/none of the above"

    idx = item.get("correct_index")
    if isinstance(idx, str) and idx.strip().isdigit():
        idx = int(idx.strip())
    if isinstance(idx, bool) or not isinstance(idx, int) or not 0 <= idx <= 3:
        return "bad correct_index"

    explanation = _clean(item.get("explanation"))
    if not explanation:
        return "missing explanation"
    if _grounded_ratio(options[idx], vocab) < 0.5 and _grounded_ratio(explanation, vocab) < 0.6:
        return "answer not supported by the passage"
    return None


def _validate_written(kind: str, item: dict, vocab: set[str]) -> str | None:
    answer = _clean(item.get("model_answer"))
    low, high = (10, 600) if kind == "short" else (100, 2500)
    if not low <= len(answer) <= high:
        return "answer length"
    if _grounded_ratio(answer, vocab) < 0.4:
        return "answer not supported by the passage"
    return None