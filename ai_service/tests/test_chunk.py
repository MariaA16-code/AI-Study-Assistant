from ai_service.chunk import chunk_pages
from ai_service.extract import Page

SENTENCE = "Plants make food using sunlight. "


def make_pages():
    return [
        Page(1, SENTENCE * 40, "Chapter 1 Plants"),
        Page(2, SENTENCE * 40, "Chapter 1 Plants"),
        Page(3, "Cells are the unit of life. " * 10, "Chapter 2 Cells"),
    ]


def test_chunks_respect_max_size():
    chunks = chunk_pages(make_pages(), max_chars=500, overlap_chars=100)
    assert chunks
    assert all(len(c.text) <= 550 for c in chunks)


def test_chapters_are_not_mixed():
    chunks = chunk_pages(make_pages(), max_chars=500, overlap_chars=100)
    for c in chunks:
        if "Cells" in c.text:
            assert c.chapter == "Chapter 2 Cells"
            assert c.page_start == 3
        if "Plants" in c.text:
            assert c.chapter == "Chapter 1 Plants"


def test_indexes_are_sequential():
    chunks = chunk_pages(make_pages(), max_chars=500, overlap_chars=100)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_tiny_text_is_dropped():
    assert chunk_pages([Page(1, "Tiny.", None)]) == []


def test_toc_lines_are_dropped():
    toc = "Chapter 1 Intro ............ 5\nChapter 2 Cells ............ 9"
    assert chunk_pages([Page(1, toc, None)]) == []