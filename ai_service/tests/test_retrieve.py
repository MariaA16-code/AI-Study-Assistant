from ai_service.retrieve import retrieve, tokenize


def test_tokenize_drops_stopwords():
    assert tokenize("What is the Zebrafish?") == ["zebrafish"]


def test_keyword_finds_rare_term(stored_doc):
    result = retrieve(stored_doc, "zebrafish", k=3)
    assert result["hits"][0]["chunk_index"] == 3
    assert result["hits"][0]["keyword_score"] > 0


def test_vector_finds_paraphrase(stored_doc):
    result = retrieve(stored_doc, "How do plants produce food?", k=3)
    assert result["hits"][0]["chunk_index"] == 0


def test_coverage(stored_doc):
    assert retrieve(stored_doc, "zebrafish", k=3)["coverage"] == 1.0
    assert retrieve(stored_doc, "quantum chromodynamics", k=3)["coverage"] == 0.0


def test_unknown_document_returns_empty(fresh_store):
    assert retrieve(404, "anything")["hits"] == []