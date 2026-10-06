import logging
import re
from typing import Any, Dict, List

from backend import database as db
from backend.rag.embeddings import EmbeddingUnavailable, get_embedding

logger = logging.getLogger("groundtruth_ai")


class RetrievalUnavailable(Exception):
    """Retrieval could not run (database or embedding model failure). Not the same as 'no evidence found'."""


class RetrievedChunk(dict):
    """Chunk result supporting both dictionary and attribute-based access."""
    def __init__(self, source: str, content: str, score: float = 0.0, chunk_number: int = 1, distance: float = 0.0):
        super().__init__(source=source, content=content, score=score, chunk_number=chunk_number, distance=distance)
        self.source = source
        self.content = content
        self.score = score
        self.chunk_number = chunk_number
        self.distance = distance


_STOP_WORDS = {'what', 'which', 'where', 'when', 'who', 'whom', 'how', 'why', 'that', 'this', 'these', 'those',
               'the', 'and', 'its', 'for', 'with', 'from', 'into', 'does', 'did', 'are', 'was', 'were', 'been',
               'have', 'has', 'had', 'tell', 'about', 'explain', 'describe'}


def _stems(text: str) -> set:
    """Lower-cased 5-character prefixes of the words in `text` (crude stemming for keyword mode)."""
    words = {w for w in re.findall(r'\b[a-zA-Z]{3,}\b', (text or "").lower())}
    return {w[:5] if len(w) >= 5 else w for w in words}


def _vector_search(query: str, top_k: int) -> List[RetrievedChunk]:
    """Cosine-distance search with pgvector; `score` is the cosine similarity (1 - distance)."""
    query_vector = str(get_embedding(query))
    with db.db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            WITH q AS (SELECT %s::vector AS v)
            SELECT source, chunk_number, content,
                   (embedding <=> q.v) AS distance,
                   1 - (embedding <=> q.v) AS score
            FROM document_chunks, q
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> q.v
            LIMIT %s;
            """,
            (query_vector, top_k),
        )
        rows = cur.fetchall()
        cur.close()
    return [RetrievedChunk(source=r["source"], content=r["content"], score=float(r["score"]),
                           chunk_number=int(r["chunk_number"]), distance=float(r["distance"])) for r in rows]


def _keyword_search(query: str, top_k: int) -> List[RetrievedChunk]:
    """Degraded-mode ranking used only on the SQLite fallback: overlap of 5-character word stems.
    `score` is the fraction of query stems found in the chunk (a lexical score, not a cosine similarity)."""
    q_words = {w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()) if w not in _STOP_WORDS}
    q_stems = {w[:5] if len(w) >= 5 else w for w in q_words} or _stems(query)
    with db.db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT source, chunk_number, content FROM document_chunks;")
        rows = cur.fetchall()
        cur.close()
    scored = []
    for row in rows:
        matches = len(q_stems & _stems(row["content"]))
        if q_stems & _stems(row["source"]):
            matches += 3
        if matches == 0:
            continue
        score = round(min(1.0, matches / max(len(q_stems), 1)), 4)
        scored.append((matches, score, row))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [RetrievedChunk(source=r["source"], content=r["content"], score=s,
                           chunk_number=int(r["chunk_number"]), distance=round(1.0 - s, 4))
            for _, s, r in scored[:top_k]]


def retrieve_context(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Top-k evidence chunks for `query`. Returns [] only when nothing matches (e.g. empty knowledge base);
    raises RetrievalUnavailable when the database or embedding model fails."""
    top_k = top_k or 3
    try:
        if db.is_postgres():
            return _vector_search(query, top_k)
        return _keyword_search(query, top_k)
    except (db.DatabaseUnavailable, EmbeddingUnavailable) as exc:
        raise RetrievalUnavailable(str(exc)) from exc
    except Exception as exc:  # driver-level errors (e.g. connection dropped mid-query)
        logger.exception("Retrieval failed")
        raise RetrievalUnavailable("retrieval query failed") from exc
