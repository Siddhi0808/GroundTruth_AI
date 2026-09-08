import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import init_db, get_connection
from backend.rag.retriever import retriever

def seed_sample_data():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM document_chunks;")
    row = cursor.fetchone()
    count = row[0] if isinstance(row, (list, tuple)) else (list(row.values())[0] if isinstance(row, dict) else row["COUNT(*)"])
    if count == 0:
        sample_content = (
            "Alexander Graham Bell was a Scottish-born inventor. "
            "He is widely credited with inventing the first practical telephone. "
            "Bell received a patent for the telephone in 1876."
        )
        is_postgres = hasattr(conn, "status") or "psycopg" in str(type(conn)).lower()
        if is_postgres:
            from backend.rag.embeddings import get_embedding
            emb = get_embedding(sample_content)
            cursor.execute(
                "INSERT INTO document_chunks (source, file_hash, chunk_number, content, embedding) VALUES (%s, %s, %s, %s, %s::vector)",
                ("telephone.txt", "sample_hash", 1, sample_content, str(emb))
            )
        else:
            cursor.execute(
                "INSERT INTO document_chunks (source, file_hash, chunk_number, content) VALUES (?, ?, ?, ?)",
                ("telephone.txt", "sample_hash", 1, sample_content)
            )
        conn.commit()
    cursor.close()
    conn.close()

def test_retriever_query():
    seed_sample_data()
    query = "Who invented the telephone?"
    results = retriever.retrieve(query, top_k=3)
    print("\nRetrieved Chunks:\n")
    for row in results:
        print("=" * 60)
        print(f"Source   : {row.source}")
        print(f"Chunk    : {row.chunk_number}")
        print(f"Score    : {row.score}")
        print(f"Distance : {row.distance:.4f}")
        print(row.content[:200] + "...\n")
    assert len(results) > 0

if __name__ == "__main__":
    test_retriever_query()
