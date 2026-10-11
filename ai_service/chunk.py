"""Cut pages into overlapping chunks that keep page range and chapter."""
import re
from dataclasses import dataclass

from .extract import TOC_RE, Page

_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass
class Chunk:
    index: int
    text: str
    page_start: int
    page_end: int
    chapter: str | None


def _split_units(text: str, cap: int) -> list[str]:
    """Sentences/lines, with very long ones cut so none exceeds `cap`."""
    units = []
    for unit in _SPLIT_RE.split(text):
        unit = unit.strip()
        if TOC_RE.search(unit):  # skip table-of-contents lines (dot leaders)
            continue
        while len(unit) > cap:
            cut = unit.rfind(" ", 0, cap)
            cut = cut if cut > 0 else cap
            units.append(unit[:cut].strip())
            unit = unit[cut:].strip()
        if unit:
            units.append(unit)
    return units


def chunk_pages(
    pages: list[Page],
    max_chars: int = 900,
    overlap_chars: int = 150,
    min_chars: int = 40,
) -> list[Chunk]:
    if overlap_chars >= max_chars // 2:
        raise ValueError("overlap_chars must be less than half of max_chars")
    unit_cap = max_chars - overlap_chars

    chunks: list[Chunk] = []
    buf: list[tuple[str, int]] = []  # (unit, page number)
    buf_len = 0
    fresh = 0  # units added since the last flush
    chapter: str | None = None

    def flush(keep_overlap: bool) -> None:
        nonlocal buf, buf_len, fresh
        if fresh:
            text = " ".join(u for u, _ in buf).strip()
            if len(text) >= min_chars:
                chunks.append(
                    Chunk(len(chunks), text, buf[0][1], buf[-1][1], chapter)
                )
        tail: list[tuple[str, int]] = []
        size = 0
        if keep_overlap and fresh:
            for unit, pg in reversed(buf):
                if size + len(unit) > overlap_chars:
                    break
                tail.insert(0, (unit, pg))
                size += len(unit)
        buf, buf_len, fresh = tail, size, 0

    for page in pages:
        if page.chapter != chapter:
            flush(keep_overlap=False)  # never mix two chapters
            chapter = page.chapter
        for unit in _split_units(page.text, unit_cap):
            if buf and buf_len + len(unit) > max_chars:
                flush(keep_overlap=True)
            buf.append((unit, page.number))
            buf_len += len(unit)
            fresh += 1
    flush(keep_overlap=False)
    return chunks