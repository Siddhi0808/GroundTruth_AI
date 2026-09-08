import logging
from typing import List, Dict, Any
from backend.database import get_connection
from backend.rag.embeddings import get_embedding

logger = logging.getLogger("groundtruth_ai")

class RetrievedChunk(dict):
    """Chunk result supporting both dictionary and attribute-based access."""
    def __init__(self, source: str, content: str, score: float = 0.0, chunk_number: int = 1, distance: float = 0.0):
        super().__init__(source=source, content=content, score=score, chunk_number=chunk_number, distance=distance)
        self.source = source
        self.content = content
        self.score = score
        self.chunk_number = chunk_number
        self.distance = distance

def retrieve_context(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    top_k = top_k or 3
    query_vector = get_embedding(query)
    results = []

    try:
        conn = get_connection()
        cursor = conn.cursor()

        is_postgres = hasattr(conn, "status") or "psycopg" in str(type(conn)).lower()

        if is_postgres:
            # PostgreSQL pgvector similarity query
            query_sql = """
                SELECT source, chunk_number, content,
                       (embedding <=> %s::vector) as distance,
                       1 - (embedding <=> %s::vector) as score
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """
            cursor.execute(query_sql, (str(query_vector), str(query_vector), str(query_vector), top_k))
            rows = cursor.fetchall()

            for row in rows:
                src = row.get("source") if isinstance(row, dict) else row[0]
                chk = row.get("chunk_number", 1) if isinstance(row, dict) else row[1]
                cnt = row.get("content") if isinstance(row, dict) else row[2]
                dist = float(row.get("distance", 0.0) if isinstance(row, dict) else row[3])
                scr = float(row.get("score", 0.0) if isinstance(row, dict) else row[4])

                results.append(RetrievedChunk(
                    source=src or "Knowledge Base",
                    content=cnt or "",
                    score=float(scr or 0.0),
                    chunk_number=int(chk or 1),
                    distance=float(dist or 0.0)
                ))
        else:
            # SQLite fallback query (content-aware ranking when pgvector is not available)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks';")
            if cursor.fetchone():
                cursor.execute("SELECT source, chunk_number, content FROM document_chunks;")
                all_rows = cursor.fetchall()

                import re
                stop_words = {'what', 'which', 'where', 'when', 'who', 'whom', 'how', 'why', 'that', 'this', 'these', 'those', 'the', 'and', 'its', 'for', 'with', 'from', 'into', 'does', 'did', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'tell', 'about', 'explain', 'describe', 'research', 'according', 'verified', 'reference', 'documentation'}
                q_words = {w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()) if w not in stop_words}
                if not q_words:
                    q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
                q_stems = {w[:5] if len(w) >= 5 else w for w in q_words}

                scored_rows = []
                for row in all_rows:
                    src = row["source"] if hasattr(row, "keys") else (row[0] if isinstance(row, tuple) else row.get("source"))
                    chk = row["chunk_number"] if hasattr(row, "keys") else (row[1] if isinstance(row, tuple) else row.get("chunk_number", 1))
                    cnt = row["content"] if hasattr(row, "keys") else (row[2] if isinstance(row, tuple) else row.get("content"))
                    cnt_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', (cnt or "").lower()))
                    cnt_stems = {w[:5] if len(w) >= 5 else w for w in cnt_words}
                    match_count = len(q_stems & cnt_stems) if q_stems else 0

                    src_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', (src or "").lower()))
                    src_stems = {w[:5] if len(w) >= 5 else w for w in src_words}
                    if q_stems & src_stems:
                        match_count += 3

                    score = round(min(0.95, 0.60 + (match_count / max(len(q_stems), 1)) * 0.35), 4) if match_count > 0 else 0.50
                    scored_rows.append((match_count, score, src, chk, cnt))

                # Order by match relevance descending, then take top_k
                scored_rows.sort(key=lambda x: (x[0], x[1]), reverse=True)
                for item in scored_rows[:top_k]:
                    results.append(RetrievedChunk(
                        source=item[2] or "Knowledge Base",
                        content=item[4] or "",
                        score=item[1],
                        chunk_number=int(item[3] or 1),
                        distance=round(1.0 - item[1], 4)
                    ))

        cursor.close()
        conn.close()

    except Exception as e:
        logger.warning(f"Vector search exception: {e}")

    return results

class ContextRetriever:
    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        return retrieve_context(query, top_k=top_k)

retriever = ContextRetriever()