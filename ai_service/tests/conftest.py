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
CHUNK_A = (
    "Photosynthesis is the process by which green plants make their own food. "
    "Chlorophyll in the leaves absorbs sunlight, and the plant uses that energy to turn "
    "water from the soil and carbon dioxide from the air into glucose and oxygen. "
    "The oxygen is released into the air through tiny pores called stomata."
)
CHUNK_B = (
    "Mitochondria are the organelles that release energy inside animal and plant cells. "
    "They break down glucose in a process called cellular respiration, and the energy "
    "released is stored in molecules of ATP. Cells with a high energy demand, such as "
    "muscle cells, contain many mitochondria."
)
CHUNK_C = (
    "The nucleus is the control centre of the cell. It contains the DNA that carries "
    "genetic instructions and it is surrounded by a double membrane called the nuclear "
    "envelope. Messages leave the nucleus through small pores, and they direct the "
    "production of proteins in the cytoplasm of the cell."
)


@pytest.fixture
def big_doc(fresh_store):
    fresh_store.store_chunks(
        2,
        [
            Chunk(0, CHUNK_A, 1, 1, "Chapter 1 Plants"),
            Chunk(1, CHUNK_B, 2, 2, "Chapter 2 Cells"),
            Chunk(2, CHUNK_C, 3, 3, "Chapter 2 Cells"),
        ],
    )
    return 2