"""Helpers for working with more than one document at a time."""
import logging
from concurrent.futures import ThreadPoolExecutor

from . import settings

logger = logging.getLogger(__name__)

MAX_PARALLEL = 3  # most documents generated at the same time (lower it if the LLM rate-limits)
_TYPES = ("mcq", "short", "long", "mixed")
_LEVELS = ("low", "medium", "high")

_ERROR_TEXT = {
    "llm_unavailable": "the AI service was not available",
    "no_content": "no usable text was found",
    "chapter_not_found": "the chapter was not found",
}


def as_ids(document_id) -> list:
    """One id or a list of ids -> a list of unique ids, in the order given."""
    if isinstance(document_id, (list, tuple, set, frozenset)):
        items = list(document_id)
    else:
        items = [document_id]
    ids, seen = [], set()
    for item in items:
        if item is None or item in seen:
            continue
        seen.add(item)
        ids.append(item)
    return ids


def split_count(count: int, parts: int) -> list[int]:
    """Share `count` between `parts` documents as evenly as possible (first ones get the extra)."""
    base, extra = divmod(count, parts)
    return [base + (1 if i < extra else 0) for i in range(parts)]


def interleave(lists: list[list]) -> list:
    """Take one item from each list in turn: [a1, b1, a2, b2, ...]."""
    out = []
    for rank in range(max((len(items) for items in lists), default=0)):
        for items in lists:
            if rank < len(items):
                out.append(items[rank])
    return out


def generate_many(document_ids, question_type, difficulty, count, generate_fn=None) -> dict:
    """Questions from several documents at once. The count is shared between the documents.

    Same result shape as generate(). Each item's "source" also gets a "document_id".
    The chapter filter is not used when there are several documents. Up to MAX_PARALLEL
    documents are generated at the same time, so ten files do not take ten times as long.
    """
    if generate_fn is None:
        from .generate import generate as generate_fn

    if question_type not in _TYPES:
        raise ValueError(f"question_type must be one of {', '.join(_TYPES)}.")
    if difficulty not in _LEVELS:
        raise ValueError(f"difficulty must be one of {', '.join(_LEVELS)}.")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= settings.MAX_QUESTIONS:
        raise ValueError(f"count must be a whole number from 1 to {settings.MAX_QUESTIONS}.")

    shares = split_count(count, len(document_ids))
    # fewer questions than documents: the later documents get none
    jobs = [
        (position, doc_id, share)
        for position, (doc_id, share) in enumerate(zip(document_ids, shares), start=1)
        if share > 0
    ]

    def run(job):
        _, doc_id, share = job
        try:
            return generate_fn(doc_id, question_type, difficulty, share, None)
        except Exception:  # one broken file must not lose the questions of the others
            logger.exception("Question generation failed for document %s", doc_id)
            return {"questions": [], "requested": share, "warnings": [], "error": "llm_unavailable"}

    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL, len(jobs))) as pool:
        results = list(pool.map(run, jobs))  # results keep the order of the documents

    per_document, warnings, errors = [], [], []
    for (position, doc_id, _), result in zip(jobs, results):
        items = list(result.get("questions") or [])
        for item in items:
            source = item.get("source")
            if isinstance(source, dict):
                source["document_id"] = doc_id
        per_document.append(items)
        for message in result.get("warnings") or []:
            warnings.append(f"File {position}: {message}")
        error = result.get("error")
        if error and not items:
            errors.append(error)
            reason = _ERROR_TEXT.get(error, error)
            warnings.append(f"File {position}: no questions could be made ({reason}).")

    questions = interleave(per_document)
    result = {"questions": questions, "requested": count, "warnings": warnings}
    if not questions:
        if "llm_unavailable" in errors:
            result["error"] = "llm_unavailable"
        else:
            result["error"] = errors[0] if errors else "no_content"
    return result