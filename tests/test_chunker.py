"""B08: chunks must fit the embedding model's 256-token window (no silent truncation)."""
import pytest

from backend import config
from backend.rag.chunker import MODEL_MAX_TOKENS, DocumentChunker, chunk_text, token_length

LONG_TEXT = " ".join(
    f"Sentence number {i} describes the thermohaline circulation of the ocean and its density gradients."
    for i in range(300)
)


def test_every_chunk_fits_the_model_window():
    chunks = chunk_text(LONG_TEXT)
    assert len(chunks) > 5
    assert max(token_length(c) for c in chunks) <= config.CHUNK_SIZE_TOKENS
    assert config.CHUNK_SIZE_TOKENS + 2 <= MODEL_MAX_TOKENS  # +[CLS]/[SEP]


def test_real_corpus_document_fits_window():
    path = config.BASE_DIR / "data" / "documents" / "telephone.txt"  # tracked in git
    chunks = chunk_text(path.read_text(encoding="utf-8"))
    assert chunks and all(token_length(c) <= config.CHUNK_SIZE_TOKENS for c in chunks)


def test_consecutive_chunks_overlap():
    chunks = chunk_text(LONG_TEXT)
    tail_words = chunks[0].split()[-5:]
    assert " ".join(tail_words) in chunks[1], "expected the end of chunk 1 to reappear at the start of chunk 2"


def test_short_text_is_one_chunk_and_no_empty_chunks():
    assert chunk_text("Bell received a patent for the telephone in 1876.") == [
        "Bell received a patent for the telephone in 1876."
    ]
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_chunk_size_above_model_limit_is_rejected():
    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=300, chunk_overlap=20)
