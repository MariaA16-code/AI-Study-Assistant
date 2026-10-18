"""answer_question: retrieve passages, ask the LLM, return answer + sources."""
import json
import logging
import re

from . import settings
from .generate import list_chapters
from .llm import LLMError, ask_llm
from .prompts import SYSTEM_ANSWER, build_answer_prompt
from .retrieve import retrieve, tokenize
from .store import get_all_chunks
from .summarize import summarize, wants_overview

logger = logging.getLogger(__name__)

NOT_FOUND_TEXT = "I couldn't find this in the uploaded material."
MAX_SOURCES = 3

# Text that extract.py writes for a described picture or page starts with this mark.
FIGURE_MARK = "[Figure]"
MAX_FIGURE_CHUNKS = 4  # most figure descriptions sent with one question
_IMAGE_RE = re.compile(
    r"\b(images?|pictures?|figures?|fig|diagrams?|charts?|graphs?|screenshots?|"
    r"photos?|illustrations?|flowcharts?|drawings?)\b",
    re.IGNORECASE,
)


def asks_about_image(question: str) -> bool:
    """Does the question talk about a picture, figure, diagram or chart?"""
    return bool(_IMAGE_RE.search(question or ""))


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


def _summary_result(res: dict) -> dict:
    text = res["summary"]
    if res["key_points"]:
        text += "\n\nKey points:\n" + "\n".join(f"• {p}" for p in res["key_points"])
    return {"answer": text, "found": True, "sources": res["sources"], "mode": "summary"}


def _figure_hits(document_id: int, question: str) -> list[dict]:
    """Figure descriptions (and the chunk after each) that best fit the question."""
    chunks = get_all_chunks(document_id)
    figures = [c for c in chunks if FIGURE_MARK in c["text"]]
    if not figures:
        return []
    by_index = {c["chunk_index"]: c for c in chunks}
    q_tokens = set(tokenize(question))
    # best word overlap first; ties keep document order (sort is stable)
    ranked = sorted(figures, key=lambda c: -len(q_tokens & set(tokenize(c["text"]))))
    picked: list[dict] = []
    for c in ranked[:MAX_FIGURE_CHUNKS]:
        picked.append(c)
        nxt = by_index.get(c["chunk_index"] + 1)
        if nxt is not None and nxt["page_start"] <= c["page_end"]:  # same page only
            picked.append(nxt)
    return picked


def _merge(first: list[dict], second: list[dict]) -> list[dict]:
    merged, seen = [], set()
    for h in first + second:
        if h["chunk_index"] not in seen:
            seen.add(h["chunk_index"])
            merged.append(h)
    return merged[: settings.TOP_K + 2 * MAX_FIGURE_CHUNKS]


def answer(document_id: int, question: str) -> dict:
    question = (question or "").strip()
    if not question:
        return _not_found()

    # "What is this document about?" / "Summarize chapter 3": retrieval cannot answer these.
    overview, chapter = wants_overview(question, list_chapters(document_id))
    if overview:
        res = summarize(document_id, chapter)
        if not res.get("error"):
            return _summary_result(res)
        if res["error"] == "llm_unavailable":
            return _not_found(error="llm_unavailable")
        # any other problem: fall back to the normal question path below

    result = retrieve(document_id, question, k=settings.TOP_K)
    hits = result["hits"]

    # Questions about a picture: always show the model the figure descriptions.
    figure_hits = _figure_hits(document_id, question) if asks_about_image(question) else []
    if figure_hits:
        hits = _merge(figure_hits, hits)  # figures first; skip the MIN_SCORE cutoff
    # Cheap guard: nothing even loosely related, so skip the LLM call.
    elif not hits or result["best_vector_score"] < settings.MIN_SCORE:
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
    sources, seen = [], set()
    for h in chosen:
        key = (h["chapter"], h["page_start"])
        if key not in seen:
            seen.add(key)
            sources.append(_source(h))
    return {"answer": text, "found": True, "sources": sources}