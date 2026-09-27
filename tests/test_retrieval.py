"""Retrieval on both backends, plus explicit failure (B10/B18) instead of silently returning []."""
import pytest

from backend import database
from backend.rag import retriever as retriever_mod
from backend.rag.embeddings import EmbeddingUnavailable
from backend.rag.retriever import RetrievalUnavailable, retrieve_context


@pytest.mark.parametrize("query, expected_source", [
    ("Who invented the telephone?", "telephone.txt"),
    ("Who discovered penicillin?", "penicillin.txt"),
    ("How long is a day on Venus?", "venus.txt"),
])
def test_top1_is_the_relevant_document(seeded, query, expected_source):
    results = retrieve_context(query, top_k=3)
    assert results and results[0]["source"] == expected_source


def test_vector_scores_are_cosine_similarities_in_rank_order(seeded):
    if seeded != "postgres":
        pytest.skip("vector scores only exist on PostgreSQL")
    scores = [r["score"] for r in retrieve_context("telephone patent", top_k=3)]
    assert scores == sorted(scores, reverse=True)
    assert all(-1.0 <= s <= 1.0 for s in scores)


def test_keyword_mode_excludes_zero_overlap_chunks(seeded):
    if seeded != "sqlite":
        pytest.skip("keyword mode is the SQLite fallback")
    assert retrieve_context("xylophone orchestration", top_k=3) == []


def test_empty_knowledge_base_returns_no_evidence(db_backend):
    assert retrieve_context("Who invented the telephone?", top_k=3) == []


def test_database_failure_raises_instead_of_returning_empty(db_backend, monkeypatch):
    def broken():
        raise database.DatabaseUnavailable("down")
    monkeypatch.setattr(database, "get_connection", broken)
    with pytest.raises(RetrievalUnavailable):
        retrieve_context("anything", top_k=3)


def test_embedding_failure_raises(pg_backend, monkeypatch):
    def broken(_text):
        raise EmbeddingUnavailable("model missing")
    monkeypatch.setattr(retriever_mod, "get_embedding", broken)
    with pytest.raises(RetrievalUnavailable):
        retrieve_context("anything", top_k=3)
