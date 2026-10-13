"""summarize_document: overview of a whole document or one chapter."""
import logging
import re

from . import settings
from .generate import _select_pool
from .llm import LLMError, ask_llm
from .prompts import SYSTEM_SUMMARY, build_summary_prompt
from .retrieve import tokenize
from .store import get_all_chunks
from .util import extract_json

logger = logging.getLogger(__name__)

MAX_SOURCES = 8

_OVERVIEW_RE = re.compile(
    r"\b(summari[sz]e|summary|overview|main (?:topic|idea|point|theme)s?|"
    r"key (?:points?|takeaways?)|gist)\b"
    r"|\bwhat\b.{0,25}\b(?:document|book|file|notes|material|pdf|paper|thesis|text)\b"
    r".{0,20}\b(?:about|cover|covers|contain|contains|discuss|discusses)\b",
    re.IGNORECASE,
)
_CHAPTER_NUM_RE = re.compile(r"\bchapter\s+(\d+)\b", re.IGNORECASE)
_GENERIC = frozenset(
    "summarize summarise summary summaries overview main topic topics idea ideas point "
    "points theme themes key takeaway takeaways gist document book file notes material "
    "pdf paper thesis text whole entire about cover covers contain contains discuss "
    "discusses brief short quick give tell write provide project chapter chapters "
    "please".split()
)


def wants_overview(question: str, chapters: list[str]) -> tuple[bool, str | None]:
    """Is this a 'what is this document about / summarize ...' question?

    Returns (True, chapter name or None). A question with a specific subject
    ("Summarize the conclusion of the project") is NOT an overview question and
    goes through normal retrieval instead.
    """
    q = question.lower()
    if not _OVERVIEW_RE.search(q):
        return False, None
    m = _CHAPTER_NUM_RE.search(q)
    if m:
        for name in chapters:
            if re.match(rf"chapter\s+{m.group(1)}\b", name, re.IGNORECASE):
                return True, name
        return False, None  # asks about a chapter this document does not have
    if any(t not in _GENERIC for t in tokenize(q)):
        return False, None
    return True, None


def _pick(pool: list[dict], k: int) -> list[dict]:
    """k passages in document order: one per chapter first, then evenly spaced."""
    n = len(pool)
    if n <= k:
        return list(pool)
    firsts: list[int] = []
    seen = set()
    for i, c in enumerate(pool):
        if c["chapter"] not in seen:
            seen.add(c["chapter"])
            firsts.append(i)
    if len(firsts) >= k:
        picked = {firsts[(j * len(firsts)) // k] for j in range(k)}
    else:
        picked = set(firsts)
        rest = [i for i in range(n) if i not in picked]
        need = k - len(picked)
        picked |= {rest[(j * len(rest)) // need] for j in range(need)}
    return [pool[i] for i in sorted(picked)]


def _sources(passages: list[dict]) -> list[dict]:
    seen, out = set(), []
    for h in passages:
        key = (h["chapter"], h["page_start"])
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "chapter": h["chapter"],
                "page": h["page_start"],
                "page_end": h["page_end"],
                "snippet": h["text"][:300],
            }
        )
    if len(out) > MAX_SOURCES:
        out = [out[(i * len(out)) // MAX_SOURCES] for i in range(MAX_SOURCES)]
    return out


def summarize(document_id: int, chapter: str | None = None) -> dict:
    chapter = (chapter or "").strip() or None
    result = {"summary": "", "key_points": [], "chapter": chapter, "sources": []}

    chunks = get_all_chunks(document_id)
    pool, error = _select_pool(chunks, chapter) if chunks else ([], "no_content")
    if error:
        return {**result, "error": error}

    passages = _pick(pool, settings.SUMMARY_PASSAGES)
    prompt = build_summary_prompt(passages, chapter)

    data = None
    for _ in range(2):  # one retry if the model ignores the JSON format
        try:
            raw = ask_llm(prompt, system=SYSTEM_SUMMARY, timeout=settings.GEN_TIMEOUT)
        except LLMError as exc:
            logger.warning("LLM unavailable during summary: %s", exc)
            return {**result, "error": "llm_unavailable"}
        data = extract_json(raw)
        if data and isinstance(data.get("summary"), str) and len(data["summary"].strip()) >= 40:
            break
        data = None
    if data is None:
        return {**result, "error": "bad_llm_output"}

    points = [
        p.strip()
        for p in (data.get("key_points") or [])
        if isinstance(p, str) and p.strip()
    ][:8]
    return {
        "summary": data["summary"].strip(),
        "key_points": points,
        "chapter": chapter,
        "sources": _sources(passages),
    }