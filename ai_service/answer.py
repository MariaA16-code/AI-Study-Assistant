"""answer_question: retrieve passages, ask the LLM, return answer + sources."""
import json
import logging
import re

from . import settings
from .generate import list_chapters
from .llm import LLMError, ask_llm
from .multi import as_ids, interleave
from .prompts import SYSTEM_ANSWER, build_answer_prompt
from .retrieve import retrieve, tokenize
from .store import get_all_chunks
from .summarize import summarize, wants_overview

logger = logging.getLogger(__name__)

NOT_FOUND_TEXT = "I couldn't find this in the uploaded material."
MAX_SOURCES = 3
MAX_SOURCES_MANY = 5  # when several documents are searched at once

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


def _source(hit: dict, with_document: bool = False) -> dict:
    source = {
        "chapter": hit["chapter"],
        "page": hit["page_start"],
        "page_end": hit["page_end"],
        "snippet": hit["text"][:300],
    }
    if with_document:  # only when several documents are searched, so the frontend can name the file
        source["document_id"] = hit.get("document_id")
    return source


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


def _merge(first: list[dict], second: list[dict], limit: int | None = None) -> list[dict]:
    if limit is None:
        limit = settings.TOP_K + 2 * MAX_FIGURE_CHUNKS
    merged, seen = [], set()
    for h in first + second:
        key = (h.get("document_id"), h["chunk_index"])  # chunk numbers repeat in every document
        if key not in seen:
            seen.add(key)
            merged.append(h)
    return merged[:limit]


def _tag(hits: list[dict], document_id: int, many: bool) -> list[dict]:
    """Remember which document each passage came from (only needed for several documents)."""
    if not many:
        return hits
    return [{**h, "document_id": document_id} for h in hits]


def _search(ids: list, question: str, many: bool) -> tuple[list[dict], float]:
    """Best passages for the question, and the best vector score found.

    One document: the usual top-K. Several documents: each is searched, then the best
    passages of every document are taken in turn, so no document crowds out the others.
    """
    if not many:
        result = retrieve(ids[0], question, k=settings.TOP_K)
        return result["hits"], result["best_vector_score"]
    k = max(2, -(-(settings.TOP_K + 3) // len(ids)))  # about TOP_K + 3 passages in total
    per_document, best = [], 0.0
    for doc_id in ids:
        result = retrieve(doc_id, question, k=k)
        per_document.append(_tag(result["hits"], doc_id, many))
        best = max(best, result["best_vector_score"])
    return interleave(per_document), best


def answer(document_id: int | list[int], question: str) -> dict:
    ids = as_ids(document_id)
    question = (question or "").strip()
    if not question or not ids:
        return _not_found()
    many = len(ids) > 1

    # "What is this document about?" / "Summarize chapter 3": retrieval cannot answer these.
    # A summary needs one document, so with several documents the normal path below is used.
    if not many:
        overview, chapter = wants_overview(question, list_chapters(ids[0]))
        if overview:
            res = summarize(ids[0], chapter)
            if not res.get("error"):
                return _summary_result(res)
            if res["error"] == "llm_unavailable":
                return _not_found(error="llm_unavailable")
            # any other problem: fall back to the normal question path below

    hits, best_vector_score = _search(ids, question, many)

    # Questions about a picture: always show the model the figure descriptions.
    figure_hits: list[dict] = []
    if asks_about_image(question):
        for doc_id in ids:
            figure_hits.extend(_tag(_figure_hits(doc_id, question), doc_id, many))
    if figure_hits:
        # figures first; skip the MIN_SCORE cutoff
        hits = _merge(figure_hits, hits, limit=len(hits) + 2 * MAX_FIGURE_CHUNKS * len(ids))
    # Cheap guard: nothing even loosely related, so skip the LLM call.
    elif not hits or best_vector_score < settings.MIN_SCORE:
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
    max_sources = MAX_SOURCES_MANY if many else MAX_SOURCES
    chosen = [hits[n - 1] for n in cited][:max_sources] or hits[:2]
    sources, seen = [], set()
    for h in chosen:
        key = (h.get("document_id"), h["chapter"], h["page_start"])
        if key not in seen:
            seen.add(key)
            sources.append(_source(h, with_document=many))
    return {"answer": text, "found": True, "sources": sources}