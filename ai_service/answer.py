"""answer_question: retrieve passages, ask the LLM, return answer + sources."""
import json
import logging
import re

from . import settings
from .llm import LLMError, ask_llm
from .prompts import SYSTEM_ANSWER, build_answer_prompt
from .retrieve import retrieve

logger = logging.getLogger(__name__)

NOT_FOUND_TEXT = "I couldn't find this in the uploaded material."
MAX_SOURCES = 3


def _not_found(error: str | None = None) -> dict:
    result = {"answer": NOT_FOUND_TEXT, "found": False, "sources": []}
    if error:
        result["error"] = error
    return result


def parse_answer(raw: str) -> dict | None:
    """Pull the JSON object out of the model's reply (tolerates code fences)."""
    text = re.sub(r"```(?:json)?", "", raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "found" not in data:
        return None
    found = data["found"]
    if isinstance(found, str):
        found = found.strip().lower() == "true"
    data["found"] = bool(found)
    return data


def _source(hit: dict) -> dict:
    return {
        "chapter": hit["chapter"],
        "page": hit["page_start"],
        "page_end": hit["page_end"],
        "snippet": hit["text"][:300],
    }


def answer(document_id: int, question: str) -> dict:
    question = (question or "").strip()
    if not question:
        return _not_found()

    result = retrieve(document_id, question, k=settings.TOP_K)
    hits = result["hits"]
    # Cheap guard: nothing even loosely related, so skip the LLM call.
    if not hits or result["best_vector_score"] < settings.MIN_SCORE:
        return _not_found()

    prompt = build_answer_prompt(question, hits)
    data = None
    for _ in range(2):  # one retry if the model ignores the JSON format
        try:
            raw = ask_llm(prompt, system=SYSTEM_ANSWER)
        except LLMError as exc:
            logger.warning("LLM unavailable: %s", exc)
            return _not_found(error="llm_unavailable")
        data = parse_answer(raw)
        if data is not None:
            break
    if data is None:
        return _not_found(error="bad_llm_output")

    text = str(data.get("answer") or "").strip()
    if not data["found"] or not text:
        return _not_found()

    cited: list[int] = []
    for n in data.get("sources") or []:
        try:
            n = int(n)
        except (TypeError, ValueError):
            continue
        if 1 <= n <= len(hits) and n not in cited:
            cited.append(n)
    chosen = [hits[n - 1] for n in cited][:MAX_SOURCES] or hits[:2]
    return {"answer": text, "found": True, "sources": [_source(h) for h in chosen]}