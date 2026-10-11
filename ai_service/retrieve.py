"""Hybrid search: vector similarity (meaning) + BM25 (exact words), merged with RRF."""
import re

from . import store

RRF_K = 60
_WORD_RE = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an the is are was were be been being am of in on at to for from by with and or "
    "as it its this that these those what which who whom how why when where do does "
    "did can could should would will shall about into than then there their they them "
    "you your i me my we our he she his her not no yes if so but".split()
)


def tokenize(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOP and len(w) > 1]


def _keyword_scores(chunk_tokens: list[list[str]], q_tokens: list[str]) -> list[float]:
    if not q_tokens or not any(chunk_tokens):
        return [0.0] * len(chunk_tokens)
    from rank_bm25 import BM25Plus  # positive weights even for tiny documents

    return [float(s) for s in BM25Plus(chunk_tokens).get_scores(q_tokens)]


def retrieve(document_id: int, question: str, k: int = 5) -> dict:
    """Returns {"hits": [...], "best_vector_score": float, "coverage": float}.

    coverage = share of the question's content words that appear anywhere in
    the document (a diagnostic; we do not gate on it yet).
    """
    chunks = store.get_all_chunks(document_id)
    if not chunks:
        return {"hits": [], "best_vector_score": 0.0, "coverage": 0.0}

    vec_hits = store.query_vectors(document_id, question, n_results=max(2 * k, 10))
    vec_rank = {h["chunk_index"]: (r, h["score"]) for r, h in enumerate(vec_hits)}

    chunk_tokens = [tokenize(c["text"]) for c in chunks]
    q_tokens = tokenize(question)
    q_set = set(q_tokens)
    kw_scores = _keyword_scores(chunk_tokens, q_tokens)

    # Only chunks that really contain a query word take part in the keyword ranking.
    matching = [i for i, toks in enumerate(chunk_tokens) if q_set & set(toks)]
    matching.sort(key=lambda i: kw_scores[i], reverse=True)
    matching = matching[: 2 * k]
    kw_score_by_index = {chunks[i]["chunk_index"]: kw_scores[i] for i in matching}

    fused: dict[int, float] = {}
    for ci, (rank, _) in vec_rank.items():
        fused[ci] = fused.get(ci, 0.0) + 1.0 / (RRF_K + rank + 1)
    for rank, i in enumerate(matching):
        ci = chunks[i]["chunk_index"]
        fused[ci] = fused.get(ci, 0.0) + 1.0 / (RRF_K + rank + 1)

    by_index = {c["chunk_index"]: c for c in chunks}
    hits = []
    for ci in sorted(fused, key=fused.get, reverse=True)[:k]:
        hit = dict(by_index[ci])
        hit["vector_score"] = vec_rank[ci][1] if ci in vec_rank else None
        hit["keyword_score"] = round(kw_score_by_index.get(ci, 0.0), 3)
        hit["fused"] = round(fused[ci], 4)
        hits.append(hit)

    vocab = set().union(*map(set, chunk_tokens))
    coverage = len(q_set & vocab) / len(q_set) if q_set else 0.0
    best_vector = vec_hits[0]["score"] if vec_hits else 0.0
    return {"hits": hits, "best_vector_score": best_vector, "coverage": round(coverage, 2)}