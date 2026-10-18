"""Read PDF / DOCX / TXT into pages with page numbers and chapter hints."""
import hashlib
import io
import logging
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

from . import settings

logger = logging.getLogger(__name__)

MIN_TEXT_CHARS = 20  # a PDF page with less text than this is treated as a scanned image
PAGE_CHARS = 3000  # DOCX/TXT have no real pages, so we make ~3000-char sections
CHAPTER_RE = re.compile(r"^(chapter|unit|lesson)\s+(\d+|[ivxlc]+)\b", re.IGNORECASE)
# Table-of-contents entries: dot leaders, or a chapter/section entry ending in a page number
TOC_RE = re.compile(
    r"([.…·]\s?){4,}"  # leaders like ...... or ………
    r"|^\s*((chapter|unit|lesson)\s+\w+|\d+(\.\d+)+)\b.*(\t| {2,})\s*(\d+|[ivxlc]+)\s*$"
    r"|^[^\t]{2,80}\t\s*(\d{1,3}|[ivxlc]{1,6})\s*$",  # short line, tab, page number
    re.IGNORECASE,
)
_BARE_HEADING_RE = re.compile(r"(chapter|unit|lesson)\s+(\d+|[ivxlc]+)\.?", re.IGNORECASE)


def _is_chapter_line(line: str) -> bool:
    line = line.strip()
    if not CHAPTER_RE.match(line) or TOC_RE.search(line):
        return False
    if _BARE_HEADING_RE.fullmatch(line):  # just "Chapter 3" or "Chapter 3."
        return True
    # a heading is short and does not read like a sentence
    return len(line) <= 80 and not line.endswith((".", "!", "?", ":"))


@dataclass
class Page:
    number: int  # 1-based page (or section) number
    text: str
    chapter: str | None = None


@dataclass
class ExtractedDocument:
    pages: list[Page]
    warnings: list[str] = field(default_factory=list)


def _detect_chapter(text: str) -> str | None:
    for line in text.splitlines()[:8]:  # headings sit near the top of a page
        line = line.strip()
        if _is_chapter_line(line):
            return line[:80]
    return None


_ocr_lock = threading.Lock()
_ocr_engine = None


def _get_ocr_engine():
    """Load the OCR engine once. Raises ImportError when rapidocr is not installed."""
    global _ocr_engine
    with _ocr_lock:
        if _ocr_engine is None:
            from rapidocr import RapidOCR

            _ocr_engine = RapidOCR(params={"Global.log_level": "error"})
        return _ocr_engine


def _boxes_to_text(items: list[tuple[float, float, float, float, str]]) -> str:
    """Turn OCR boxes (x0, y0, x1, y1, text) into lines of text.

    Boxes on the same line are joined in reading order. A wide gap between two boxes
    (a table column) is written as ' | ', so table rows keep their cells apart.
    """
    if not items:
        return ""
    heights = sorted(y1 - y0 for _, y0, _, y1, _ in items)
    median = heights[len(heights) // 2] or 1.0

    def centre(item):
        return (item[1] + item[3]) / 2

    rows: list[list] = []
    current: list = []
    for item in sorted(items, key=centre):
        if current and abs(centre(item) - sum(centre(c) for c in current) / len(current)) > 0.6 * median:
            rows.append(current)
            current = []
        current.append(item)
    if current:
        rows.append(current)

    lines = []
    for row in rows:
        row.sort(key=lambda it: it[0])
        parts = [row[0][4]]
        for prev, nxt in zip(row, row[1:]):
            parts.append(" | " if nxt[0] - prev[2] > 2 * median else " ")
            parts.append(nxt[4])
        line = "".join(parts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _ocr_image(image) -> str:
    """Read the text in a PIL image with OCR. Raises ImportError when rapidocr is not installed."""
    import numpy as np

    engine = _get_ocr_engine()
    result = engine(np.array(image.convert("RGB")))
    if result is None or result.boxes is None or result.txts is None:
        return ""
    items = []
    for box, text, score in zip(result.boxes, result.txts, result.scores):
        if float(score) < 0.5 or not str(text).strip():  # skip uncertain noise
            continue
        xs = [pt[0] for pt in box]
        ys = [pt[1] for pt in box]
        items.append((min(xs), min(ys), max(xs), max(ys), str(text).strip()))
    return _boxes_to_text(items)


def _ocr_page_text(page) -> str:
    """Read a scanned PDF page with OCR."""
    return _ocr_image(page.to_image(resolution=settings.OCR_DPI).original)


def _read_pdf(path: Path) -> tuple[list[Page], list[str]]:
    import pdfplumber

    pages: list[Page] = []
    empty = ocr_used = ocr_skipped = 0
    ocr_missing = False
    with pdfplumber.open(str(path)) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            text = (p.extract_text() or "").strip()
            if len(text) < MIN_TEXT_CHARS and settings.OCR_ENABLED and not ocr_missing:
                if ocr_used >= settings.OCR_MAX_PAGES:
                    ocr_skipped += 1
                else:
                    try:
                        ocr_text = _ocr_page_text(p)
                        if len(ocr_text) > len(text):
                            text = ocr_text
                            ocr_used += 1
                    except ImportError:
                        ocr_missing = True
                    except Exception:
                        logger.exception("OCR failed on page %s of %s", i, path.name)
            if not text:
                empty += 1
            pages.append(Page(i, text))

    current = None
    for page in pages:
        found = _detect_chapter(page.text)
        if found:
            current = found
        page.chapter = current

    warnings = []
    if ocr_used:
        warnings.append(
            f"{ocr_used} page(s) had no text layer and were read with OCR. "
            "OCR can make small mistakes, especially with tables and handwriting."
        )
    if ocr_missing:
        warnings.append("Some pages are scanned images, but OCR is not installed (pip install rapidocr).")
    if ocr_skipped:
        warnings.append(
            f"OCR was limited to {settings.OCR_MAX_PAGES} pages, so {ocr_skipped} scanned page(s) were skipped."
        )
    if pages and empty / len(pages) > 0.5:
        warnings.append(
            "Most pages have no extractable text. This looks like a scanned PDF, "
            "and OCR could not read it."
        )
    return pages, warnings


def _paragraphs_to_pages(items: list[tuple[str, bool]]) -> list[Page]:
    """items: (text, is_heading). Groups paragraphs into ~PAGE_CHARS sections."""
    pages: list[Page] = []
    buf: list[str] = []
    size = 0
    current = None
    page_chapter = None

    def flush():
        nonlocal buf, size
        if buf:
            pages.append(Page(len(pages) + 1, "\n".join(buf), page_chapter))
        buf, size = [], 0

    for text, is_heading in items:
        if (is_heading and not TOC_RE.search(text)) or _is_chapter_line(text):
            flush()
            current = text[:80]
        if not buf:
            page_chapter = current
        buf.append(text)
        size += len(text)
        if size >= PAGE_CHARS:
            flush()
    flush()
    return pages


def _docx_blocks(document):
    """Paragraphs and tables in the order they appear in the document."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


class _DocxImages:
    """Reads the text inside pictures of a DOCX with OCR. Each distinct picture is read once."""

    MIN_SIDE = 60  # smaller pictures are icons or bullets, not worth reading

    def __init__(self, document):
        self.document = document
        self.cache: dict[str, list[str]] = {}
        self.attempts = 0
        self.with_text = 0
        self.skipped = 0
        self.missing = False

    def lines(self, paragraph) -> list[str]:
        """Text lines found in the pictures of one paragraph (empty when there are none)."""
        if not settings.OCR_ENABLED or self.missing:
            return []
        found = []
        for rid in paragraph._p.xpath(".//a:blip/@r:embed"):
            part = self.document.part.related_parts.get(rid)
            if part is None:
                continue
            key = hashlib.md5(part.blob).hexdigest()
            if key not in self.cache:
                self.cache[key] = self._read(part.blob)
            found.extend(self.cache[key])
        return found

    def _read(self, blob: bytes) -> list[str]:
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(blob))
            if min(image.size) < self.MIN_SIDE:
                return []
            if self.attempts >= settings.OCR_MAX_IMAGES:
                self.skipped += 1
                return []
            self.attempts += 1
            text = _ocr_image(image)
        except ImportError:
            self.missing = True
            return []
        except Exception:  # unsupported picture formats such as EMF or WMF
            logger.warning("Could not read a picture inside the DOCX", exc_info=True)
            return []
        lines = []
        for line in text.splitlines():
            if CHAPTER_RE.match(line):  # a line inside a picture must never start a new chapter
                line = "- " + line
            lines.append(line)
        if lines:
            self.with_text += 1
        return lines


def _table_rows(table, images: "_DocxImages | None" = None) -> list[str]:
    """One text line per table row, cells joined with ' | ' (merged cells are counted once).

    Tables nested inside a cell, and text inside pictures in a cell, are read right after the row.
    """
    rows = []
    for row in table.rows:
        cells, seen, nested, extra = [], set(), [], []
        for cell in row.cells:
            if id(cell._tc) in seen:  # a merged cell shows up once per column it spans
                continue
            seen.add(id(cell._tc))
            text = " ".join(cell.text.split())
            if text:
                cells.append(text)
            nested.extend(cell.tables)
            if images is not None:
                for paragraph in cell.paragraphs:
                    extra.extend(images.lines(paragraph))
        line = " | ".join(cells)
        if line:
            if CHAPTER_RE.match(line):  # a table row must never start a new chapter
                line = "- " + line
            rows.append(line)
        rows.extend(extra)
        for inner in nested:
            rows.extend(_table_rows(inner, images))
    return rows


def _read_docx(path: Path) -> tuple[list[Page], list[str]]:
    import docx
    from docx.text.paragraph import Paragraph

    document = docx.Document(str(path))
    images = _DocxImages(document)
    items = []
    for block in _docx_blocks(document):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                style = block.style.name if block.style is not None else ""
                items.append((text, style.startswith("Heading 1")))
            items.extend((line, False) for line in images.lines(block))
        else:
            items.extend((row, False) for row in _table_rows(block, images))

    warnings = ["DOCX has no fixed pages; page numbers are approximate sections."]
    if images.with_text:
        warnings.append(
            f"{images.with_text} picture(s) in the DOCX were read with OCR. "
            "OCR can make small mistakes."
        )
    if images.missing:
        warnings.append(
            "The DOCX has pictures, but OCR is not installed, so text inside pictures "
            "is not read (pip install rapidocr)."
        )
    if images.skipped:
        warnings.append(
            f"OCR was limited to {settings.OCR_MAX_IMAGES} pictures, "
            f"so {images.skipped} picture(s) were skipped."
        )
    return _paragraphs_to_pages(items), warnings


def _read_txt(path: Path) -> tuple[list[Page], list[str]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # one item per line, so headings are found even without blank lines around them
    items = [(line.strip(), False) for line in raw.splitlines() if line.strip()]
    warnings = ["TXT has no fixed pages; page numbers are approximate sections."]
    return _paragraphs_to_pages(items), warnings


def extract_document(file_path: str) -> ExtractedDocument:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        pages, warnings = _read_pdf(path)
    elif ext == ".docx":
        pages, warnings = _read_docx(path)
    elif ext == ".txt":
        pages, warnings = _read_txt(path)
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Use PDF, DOCX or TXT.")

    if not any(p.text.strip() for p in pages):
        warnings.append("No readable text found in this file.")
    return ExtractedDocument(pages, warnings)