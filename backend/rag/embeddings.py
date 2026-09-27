import logging
import threading
from typing import List, Sequence

from sentence_transformers import SentenceTransformer

from backend import config

logger = logging.getLogger("groundtruth_ai")


class EmbeddingUnavailable(Exception):
    """Raised when the embedding model cannot be loaded or run."""


# Lazily loaded singleton. The lock matters because request handlers run in a threadpool,
# so two first requests could otherwise load the model twice.
_model = None
_model_lock = threading.Lock()
# The HuggingFace fast (Rust) tokenizer is not safe for concurrent use from several threads
# ("RuntimeError: Already borrowed"), and one model instance cannot run batches in parallel anyway,
# so all tokenizer/model calls are serialised.
_inference_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info("Loading SentenceTransformer model (%s)...", config.EMBEDDING_MODEL)
                try:
                    try:
                        _model = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)
                    except Exception:
                        _model = SentenceTransformer(config.EMBEDDING_MODEL)
                except Exception as exc:
                    raise EmbeddingUnavailable(f"could not load embedding model {config.EMBEDDING_MODEL}") from exc
    return _model


def count_tokens(text: str) -> int:
    """Word-piece tokens for `text`, excluding [CLS]/[SEP]."""
    tokenizer = get_model().tokenizer
    with _inference_lock:
        return len(tokenizer(text, add_special_tokens=False)["input_ids"])


def get_embedding(text: str) -> List[float]:
    """Dense, L2-normalised embedding for one text."""
    if not text:
        raise ValueError("cannot embed empty text")
    return get_embeddings([text])[0]


def get_embeddings(texts: Sequence[str], batch_size: int = 32) -> List[List[float]]:
    """Batch-encode texts (one forward pass per batch instead of one per text)."""
    if not texts:
        return []
    model = get_model()
    try:
        with _inference_lock:
            vectors = model.encode(list(texts), batch_size=batch_size, convert_to_numpy=True,
                                   normalize_embeddings=True, show_progress_bar=False)
    except Exception as exc:
        raise EmbeddingUnavailable("embedding inference failed") from exc
    return [v.tolist() for v in vectors]
