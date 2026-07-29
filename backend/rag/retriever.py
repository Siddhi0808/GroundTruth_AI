import logging
from typing import List, Dict, Any
from backend.database import get_connection
from backend.rag.embeddings import get_embedding

logger = logging.getLogger("groundtruth_ai")

def retrieve_context(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    query_vector = get_embedding(query)
    results = []

    try:
        conn = get_connection()
        cursor = conn.cursor()

        is_postgres = hasattr(conn, "status") or "psycopg" in str(type(conn)).lower()

        if is_postgres:
            # PostgreSQL pgvector similarity query
            query_sql = """
                SELECT source, content, 1 - (embedding <=> %s::vector) as score
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """
            cursor.execute(query_sql, (str(query_vector), str(query_vector), top_k))
            rows = cursor.fetchall()

            for row in rows:
                # Handle dictionary or tuple rows
                src = row.get("source") if isinstance(row, dict) else row[0]
                cnt = row.get("content") if isinstance(row, dict) else row[1]
                scr = row.get("score") if isinstance(row, dict) else row[2]

                results.append({
                    "source": src or "Knowledge Base",
                    "content": cnt or "",
                    "score": float(scr or 0.0)
                })
        else:
            # SQLite fallback query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks';")
            if cursor.fetchone():
                cursor.execute("SELECT source, content FROM document_chunks ORDER BY id DESC LIMIT ?;", (top_k,))
                rows = cursor.fetchall()
                for row in rows:
                    results.append({
                        "source": row[0] if isinstance(row, tuple) else row["source"],
                        "content": row[1] if isinstance(row, tuple) else row["content"],
                        "score": 0.85
                    })

        cursor.close()
        conn.close()

    except Exception as e:
        logger.warning(f"Vector search exception: {e}")

    return results