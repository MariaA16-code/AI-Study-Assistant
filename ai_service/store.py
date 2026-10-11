"""Embeddings (fastembed) + ChromaDB storage, one collection per document."""
from . import settings
from .chunk import Chunk

BATCH = 64
_model = None
_client = None


def _embedder():
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        _model = TextEmbedding(settings.EMBED_MODEL)
    return _model


def _chroma():
    global _client
    if _client is None:
        import chromadb

        _client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    return _client


def collection_name(document_id: int) -> str:
    return f"doc_{document_id}"  # ChromaDB needs 3+ characters


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _embedder().embed(texts)]


def _to_hit(text: str, meta: dict, distance: float | None = None) -> dict:
    hit = {
        "chunk_index": meta["chunk_index"],
        "text": text,
        "page_start": meta["page_start"],
        "page_end": meta["page_end"],
        "chapter": meta["chapter"] or None,  # Chroma can't store None
    }
    if distance is not None:
        # Vectors are unit length and Chroma returns squared L2 distance,
        # so cosine similarity = 1 - distance / 2.
        hit["score"] = round(1 - distance / 2, 4)
    return hit


def delete_document(document_id: int) -> None:
    name = collection_name(document_id)
    client = _chroma()
    client.get_or_create_collection(name)  # makes delete safe if it never existed
    client.delete_collection(name)


def store_chunks(document_id: int, chunks: list[Chunk]) -> int:
    delete_document(document_id)  # re-processing replaces the old data
    col = _chroma().get_or_create_collection(collection_name(document_id))
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start : start + BATCH]
        col.add(
            ids=[f"doc{document_id}_c{c.index}" for c in batch],
            embeddings=embed_texts([c.text for c in batch]),
            documents=[c.text for c in batch],
            metadatas=[
                {
                    "chunk_index": c.index,
                    "page_start": c.page_start,
                    "page_end": c.page_end,
                    "chapter": c.chapter or "",
                }
                for c in batch
            ],
        )
    return len(chunks)


def query_vectors(document_id: int, question: str, n_results: int = 8) -> list[dict]:
    col = _chroma().get_or_create_collection(collection_name(document_id))
    total = col.count()
    if total == 0:
        return []
    res = col.query(
        query_embeddings=embed_texts([question]),
        n_results=min(n_results, total),
        include=["documents", "metadatas", "distances"],
    )
    return [
        _to_hit(t, m, d)
        for t, m, d in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        )
    ]


def get_all_chunks(document_id: int) -> list[dict]:
    """Every chunk of a document in order (the keyword search needs these)."""
    col = _chroma().get_or_create_collection(collection_name(document_id))
    res = col.get(include=["documents", "metadatas"])
    hits = [_to_hit(t, m) for t, m in zip(res["documents"], res["metadatas"])]
    return sorted(hits, key=lambda h: h["chunk_index"])