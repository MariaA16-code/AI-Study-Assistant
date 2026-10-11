"""Read PDF / DOCX / TXT into pages with page numbers and chapter hints."""
import re
from dataclasses import dataclass, field
from pathlib import Path

PAGE_CHARS = 3000  # DOCX/TXT have no real pages, so we make ~3000-char sections
CHAPTER_RE = re.compile(r"^(chapter|unit|lesson)\s+(\d+|[ivxlc]+)\b", re.IGNORECASE)
TOC_RE = re.compile(r"(\.\s?){4,}")  # dot leaders like "Chapter 1 ...... 5"


def _is_chapter_line(line: str) -> bool:
    return bool(CHAPTER_RE.match(line)) and not TOC_RE.search(line)


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


def _read_pdf(path: Path) -> tuple[list[Page], list[str]]:
    import pdfplumber

    pages, empty = [], 0
    with pdfplumber.open(str(path)) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            text = (p.extract_text() or "").strip()
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
    if pages and empty / len(pages) > 0.5:
        warnings.append(
            "Most pages have no extractable text. This looks like a scanned PDF; "
            "OCR is not supported yet."
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
        if is_heading or _is_chapter_line(text):
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


def _read_docx(path: Path) -> tuple[list[Page], list[str]]:
    import docx

    document = docx.Document(str(path))
    items = []
    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name if para.style is not None else ""
        items.append((text, style.startswith("Heading 1")))

    warnings = ["DOCX has no fixed pages; page numbers are approximate sections."]
    if document.tables:
        warnings.append("Tables in the DOCX are not read yet.")
    return _paragraphs_to_pages(items), warnings


def _read_txt(path: Path) -> tuple[list[Page], list[str]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    items = [(p.strip(), False) for p in re.split(r"\n\s*\n", raw) if p.strip()]
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