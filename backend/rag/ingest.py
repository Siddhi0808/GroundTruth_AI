import hashlib
import os
from pathlib import Path

from backend.rag.document_loader import load_documents
from backend.rag.embeddings import get_embedding
from backend.database import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCUMENT_FOLDER = str(BASE_DIR / "data" / "documents")

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

def ingest():
    documents = load_documents(DOCUMENT_FOLDER)
    connection = get_connection()
    cursor = connection.cursor()

    is_postgres = hasattr(connection, "status") or "psycopg" in str(type(connection)).lower()

    if is_postgres:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                chunk_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384)
            );
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                chunk_number INTEGER NOT NULL,
                content TEXT NOT NULL
            );
        """)
    connection.commit()

    for doc in documents:
        if not doc.get("content", "").strip():
            continue

        file_hash = hashlib.md5(doc["content"].encode("utf-8")).hexdigest()

        if is_postgres:
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE source = %s;", (doc["source"],))
            row = cursor.fetchone()
            existing = list(row.values())[0] if isinstance(row, dict) else row[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE source = ?;", (doc["source"],))
            row = cursor.fetchone()
            existing = row[0] if hasattr(row, "__getitem__") else 0

        if existing:
            print(f"✓ Skipping {doc['source']} (unchanged)")
            continue

        chunks = chunk_text(doc["content"])
        print(f"{doc['source']}: {len(chunks)} chunks")

        for index, chunk in enumerate(chunks, start=1):
            embedding = get_embedding(chunk)
            if is_postgres:
                cursor.execute(
                    """
                    INSERT INTO document_chunks (source, file_hash, chunk_number, content, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    """,
                    (doc["source"], file_hash, index, chunk, str(embedding))
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO document_chunks (source, file_hash, chunk_number, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    (doc["source"], file_hash, index, chunk)
                )

        connection.commit()
        print(f"✓ Stored {doc['source']}")

    cursor.close()
    connection.close()

if __name__ == "__main__":
    ingest()