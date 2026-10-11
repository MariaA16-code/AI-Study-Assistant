import pytest

from ai_service import settings, store
from ai_service.chunk import Chunk


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr(store, "_client", None)
    return store


@pytest.fixture
def stored_doc(fresh_store):
    chunks = [
        Chunk(0, "Photosynthesis is how plants make food from sunlight, water and carbon dioxide.", 1, 1, "Chapter 1 Plants"),
        Chunk(1, "Mitochondria are the organelles that release energy inside animal cells.", 2, 2, "Chapter 2 Cells"),
        Chunk(2, "The French Revolution began in 1789 and changed the political order of Europe.", 3, 3, None),
        Chunk(3, "Zebrafish embryos are transparent, which helps researchers observe organ development.", 4, 4, "Chapter 3 Research"),
    ]
    fresh_store.store_chunks(1, chunks)
    return 1