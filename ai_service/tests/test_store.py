import pytest

from ai_service import settings, store
from ai_service.chunk import Chunk


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr(store, "_client", None)
    return store


def make_chunks():
    return [
        Chunk(0, "Photosynthesis is how plants make food from sunlight, water and carbon dioxide.", 1, 1, "Chapter 1 Plants"),
        Chunk(1, "Mitochondria are the organelles that release energy inside animal cells.", 2, 2, "Chapter 2 Cells"),
        Chunk(2, "The French Revolution began in 1789 and changed the political order of Europe.", 3, 3, None),
    ]


def test_query_finds_the_right_chunk(fresh_store):
    assert fresh_store.store_chunks(1, make_chunks()) == 3
    hits = fresh_store.query_vectors(1, "How do plants produce food?", n_results=2)
    assert hits[0]["chunk_index"] == 0
    assert hits[0]["page_start"] == 1
    assert hits[0]["chapter"] == "Chapter 1 Plants"


def test_none_chapter_roundtrip(fresh_store):
    fresh_store.store_chunks(2, make_chunks())
    hits = fresh_store.get_all_chunks(2)
    assert [h["chunk_index"] for h in hits] == [0, 1, 2]
    assert hits[2]["chapter"] is None


def test_reprocessing_replaces_old_chunks(fresh_store):
    fresh_store.store_chunks(3, make_chunks())
    fresh_store.store_chunks(3, make_chunks()[:1])
    assert len(fresh_store.get_all_chunks(3)) == 1


def test_documents_are_isolated(fresh_store):
    fresh_store.store_chunks(4, make_chunks())
    assert fresh_store.query_vectors(5, "plants") == []


def test_delete_document(fresh_store):
    fresh_store.store_chunks(6, make_chunks())
    fresh_store.delete_document(6)
    assert fresh_store.get_all_chunks(6) == []