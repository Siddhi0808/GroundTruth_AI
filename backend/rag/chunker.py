"""Token-aware chunking used by BOTH upload and batch ingestion.

all-MiniLM-L6-v2 silently truncates input beyond 256 word-piece tokens (254 content tokens + [CLS]/[SEP]).
Chunks are therefore measured with the embedding model's own tokenizer and capped at CHUNK_SIZE_TOKENS (200),
with CHUNK_OVERLAP_TOKENS (40) of overlap so a fact that straddles a boundary appears whole in at least one chunk.
The recursive splitter prefers paragraph, line and sentence boundaries before falling back to words.
"""
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend import config
from backend.rag.embeddings import count_tokens

MODEL_MAX_TOKENS = 256


def token_length(text: str) -> int:
    """Length function for the splitter: chunk size is measured in embedding-model tokens, not characters."""
    return count_tokens(text)


class DocumentChunker:
    """Recursive splitter configured for the embedding model's token limit."""
    def __init__(self, chunk_size: int = config.CHUNK_SIZE_TOKENS, chunk_overlap: int = config.CHUNK_OVERLAP_TOKENS):
        if chunk_size + 2 > MODEL_MAX_TOKENS:
            raise ValueError(f"chunk_size {chunk_size} exceeds the embedding model limit of {MODEL_MAX_TOKENS - 2}")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=token_length,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator="end",
        )

    def split(self, text: str) -> List[str]:
        """Split `text` into stripped, non-empty chunks."""
        return [c.strip() for c in self.splitter.split_text(text) if c.strip()]


chunker = DocumentChunker()


def chunk_text(text: str) -> List[str]:
    """Chunk `text` with the shared default chunker (used by upload and batch ingestion)."""
    return chunker.split(text)
