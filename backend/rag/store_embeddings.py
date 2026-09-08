import hashlib
from backend.rag.embeddings import embedding_model
from backend.database import get_connection


document = """
Alexander Graham Bell was a Scottish-born inventor.
He invented the first practical telephone.
Bell received a patent for the telephone in 1876.
"""

source = "telephone.txt"
file_hash = hashlib.md5(document.strip().encode("utf-8")).hexdigest()

embedding = embedding_model.generate_embedding(document)

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
    cursor.execute(
        """
        INSERT INTO document_chunks (source, file_hash, chunk_number, content, embedding)
        VALUES (%s, %s, %s, %s, %s::vector)
        """,
        (source, file_hash, 1, document, str(embedding))
    )
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
    cursor.execute(
        """
        INSERT INTO document_chunks (source, file_hash, chunk_number, content)
        VALUES (?, ?, ?, ?)
        """,
        (source, file_hash, 1, document)
    )

connection.commit()
cursor.close()
connection.close()

print("Document stored successfully!")