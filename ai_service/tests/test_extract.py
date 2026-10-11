import docx
import pytest

from ai_service.extract import extract_document


def test_txt_pages_and_chapters(tmp_path):
    f = tmp_path / "book.txt"
    f.write_text(
        "Chapter 1 Cells\n\nCells are the unit of life.\n\n"
        "Chapter 2 Energy\n\nPlants make food.",
        encoding="utf-8",
    )
    doc = extract_document(str(f))
    assert doc.pages[0].chapter.startswith("Chapter 1")
    assert any(p.chapter and p.chapter.startswith("Chapter 2") for p in doc.pages)
    assert "Cells are the unit of life." in doc.pages[0].text


def test_docx_heading_becomes_chapter(tmp_path):
    d = docx.Document()
    d.add_heading("Photosynthesis", level=1)
    d.add_paragraph("Plants make food using light.")
    path = tmp_path / "notes.docx"
    d.save(str(path))
    doc = extract_document(str(path))
    assert doc.pages[0].chapter == "Photosynthesis"


def test_unsupported_type(tmp_path):
    f = tmp_path / "a.xyz"
    f.write_text("x")
    with pytest.raises(ValueError):
        extract_document(str(f))


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_document("nope.pdf")

def test_toc_lines_are_not_chapters(tmp_path):
    f = tmp_path / "toc.txt"
    f.write_text(
        "Chapter 1 Intro ........ 5\n\nChapter 1 Intro\n\nReal text here.",
        encoding="utf-8",
    )
    doc = extract_document(str(f))
    assert all("...." not in (p.chapter or "") for p in doc.pages)
    assert doc.pages[-1].chapter == "Chapter 1 Intro"       