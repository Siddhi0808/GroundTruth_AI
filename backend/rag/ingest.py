"""Batch ingestion of data/documents/ and the indexing helper shared with the upload endpoint.

Usage:
    python -m backend.rag.ingest            # index files not yet in the database (dedup by content hash)
    python -m backend.rag.ingest --rebuild  # delete all chunks and re-index every file (needed after
                                            # changing chunking or the embedding model)
"""
import argparse
import logging
from typing import List

from backend import config
from backend import database as db
from backend.rag.chunker import chunk_text  # re-exported for backward compatibility
from backend.rag.document_loader import load_documents
from backend.rag.embeddings import get_embeddings

logger = logging.getLogger("groundtruth_ai")

__all__ = ["chunk_text", "prepare_chunks", "index_document", "ingest"]


def prepare_chunks(text: str):
    """Chunk and (on PostgreSQL) embed. Done before opening a transaction so the DB is not held
    during model inference. SQLite mode stores no vectors, so no embeddings are computed there."""
    chunks = chunk_text(text)
    embeddings = get_embeddings(chunks) if (chunks and db.is_postgres()) else None
    return chunks, embeddings


def index_document(conn, source: str, file_hash: str, chunks: List[str], embeddings) -> int:
    """Insert prepared chunks inside the caller's transaction. Returns rows inserted (0 if already indexed)."""
    return db.insert_chunks(conn, source, file_hash, chunks, embeddings)


def ingest(rebuild: bool = False, folder=None) -> dict:
    db.init_db()
    folder = folder or config.DOCUMENTS_DIR
    documents = load_documents(folder)
    stats = {"files": len(documents), "indexed": 0, "skipped_existing": 0, "empty": 0, "chunks": 0}

    with db.db_connection() as conn:
        if rebuild:
            cur = conn.cursor()
            cur.execute("DELETE FROM document_chunks;")
            cur.close()
            conn.commit()
            logger.info("Rebuild: deleted all existing chunks")
            db.DEDUP_CONSTRAINT_OK = db.ensure_chunk_schema(conn)

        for doc in documents:
            if not doc["content"].strip():
                stats["empty"] += 1
                logger.warning("Skipping %s: no extractable text", doc["source"])
                continue
            existing = db.find_document_by_hash(conn, doc["file_hash"])
            if existing:
                stats["skipped_existing"] += 1
                continue
            chunks, embeddings = prepare_chunks(doc["content"])
            inserted = index_document(conn, doc["source"], doc["file_hash"], chunks, embeddings)
            conn.commit()  # one transaction per document
            stats["indexed"] += 1
            stats["chunks"] += inserted
            print(f"✓ {doc['source']}: {inserted} chunks")
    print(f"Ingest complete ({db.BACKEND}): {stats}")
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rebuild", action="store_true", help="delete all chunks and re-index every file")
    ingest(rebuild=parser.parse_args().rebuild)
