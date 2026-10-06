"""Database access: backend selection (PostgreSQL + pgvector, optional SQLite fallback), schema, connections.

Design notes
- The backend is chosen once, lazily, the first time the database is used (normally at app startup).
  It is NOT re-selected at runtime: silently switching databases mid-run would split data between two stores.
- If PostgreSQL is unreachable at startup and ALLOW_SQLITE_FALLBACK is true, the app runs on SQLite in a
  degraded mode (keyword retrieval, no vectors). This is logged at ERROR level and reported by /api/health
  and in every /detect response. With ALLOW_SQLITE_FALLBACK=false, startup fails instead.
- If the selected database becomes unavailable later, callers get DatabaseUnavailable and the API returns 503.
"""
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from backend import config

logger = logging.getLogger("groundtruth_ai")


class DatabaseUnavailable(Exception):
    """Raised when the configured database cannot be reached or a query fails at the driver level."""


Base = declarative_base()


def _utcnow():
    """Naive UTC timestamp (the history column is timezone-naive on both backends)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DetectionHistory(Base):
    """One row per /detect call, including which engine produced the verdict."""
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True)
    query = Column(Text, nullable=False)
    llm_response = Column(Text, nullable=False)
    verdict = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    engine = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


# ---------------------------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------------------------
_lock = threading.Lock()
_configured = False
BACKEND: Optional[str] = None          # "postgres" | "sqlite"
DATABASE_URL: Optional[str] = None
USE_SQLITE = False
FALLBACK_ACTIVE = False
FALLBACK_REASON: Optional[str] = None
DEDUP_CONSTRAINT_OK: Optional[bool] = None
engine = None
SessionLocal = None
_sqlite_path: Optional[str] = None


def _psycopg_dsn(url: str) -> str:
    # psycopg2 understands postgresql:// URIs but not SQLAlchemy driver suffixes.
    return url.replace("postgresql+psycopg2://", "postgresql://").replace("postgres://", "postgresql://")


def _set_sqlite(path: str, fallback: bool, reason: Optional[str]):
    """Point all module-level handles at a SQLite file (explicit sqlite:// URL or degraded fallback)."""
    global BACKEND, DATABASE_URL, USE_SQLITE, FALLBACK_ACTIVE, FALLBACK_REASON, engine, SessionLocal, _sqlite_path
    _sqlite_path = path
    DATABASE_URL = f"sqlite:///{path}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    BACKEND, USE_SQLITE, FALLBACK_ACTIVE, FALLBACK_REASON = "sqlite", True, fallback, reason


def configure_database(url: Optional[str] = None, allow_fallback: Optional[bool] = None) -> None:
    """(Re)select the database backend. Called lazily; tests call it directly to point at a test DB."""
    global BACKEND, DATABASE_URL, USE_SQLITE, FALLBACK_ACTIVE, FALLBACK_REASON, engine, SessionLocal
    global _configured, DEDUP_CONSTRAINT_OK
    url = url or config.build_database_url()
    if url.startswith("postgres://"):  # SQLAlchemy 2 rejects this alias; it would look like "unreachable"
        url = "postgresql://" + url[len("postgres://"):]
    allow_fallback = config.ALLOW_SQLITE_FALLBACK if allow_fallback is None else allow_fallback
    DEDUP_CONSTRAINT_OK = None
    if engine is not None:
        engine.dispose()

    if url.startswith("sqlite:///"):
        _set_sqlite(url[len("sqlite:///"):], fallback=False, reason=None)
    else:
        try:
            pg_engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            with pg_engine.connect():
                pass
            engine = pg_engine
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            BACKEND, DATABASE_URL, USE_SQLITE, FALLBACK_ACTIVE, FALLBACK_REASON = "postgres", url, False, False, None
        except Exception as exc:
            if not allow_fallback:
                _configured = False
                raise DatabaseUnavailable("PostgreSQL is unreachable and ALLOW_SQLITE_FALLBACK is false") from exc
            logger.error(
                "PostgreSQL unreachable (%s: %s). DEGRADED MODE: using SQLite at %s with keyword retrieval "
                "(no vector search). Documents indexed here are not visible to PostgreSQL.",
                type(exc).__name__, str(exc).strip().splitlines()[0] if str(exc).strip() else "", config.SQLITE_PATH,
            )
            _set_sqlite(config.SQLITE_PATH, fallback=True, reason=f"postgres_unreachable:{type(exc).__name__}")
    _configured = True
    logger.info("Database backend: %s (fallback_active=%s)", BACKEND, FALLBACK_ACTIVE)


def ensure_configured() -> None:
    """Select the backend once, thread-safely, on first use."""
    if not _configured:
        with _lock:
            if not _configured:
                configure_database()


def is_postgres() -> bool:
    """True when the vector (pgvector) path is active."""
    ensure_configured()
    return BACKEND == "postgres"


def database_status() -> dict:
    """Backend summary used by /api/health, /detect metadata and benchmark results."""
    ensure_configured()
    return {
        "backend": BACKEND,
        "fallback_active": FALLBACK_ACTIVE,
        "fallback_reason": FALLBACK_REASON,
        "retrieval_mode": "vector" if BACKEND == "postgres" else "keyword",
        "dedup_constraint": DEDUP_CONSTRAINT_OK,
    }


# ---------------------------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------------------------
def get_db():
    """FastAPI dependency yielding an ORM session (history table)."""
    ensure_configured()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_connection():
    """Raw DB-API connection for chunk/vector queries. Prefer `db_connection()` which always closes it."""
    ensure_configured()
    try:
        if BACKEND == "sqlite":
            conn = sqlite3.connect(_sqlite_path, timeout=30)
            conn.row_factory = sqlite3.Row
            return conn
        return psycopg2.connect(_psycopg_dsn(DATABASE_URL), cursor_factory=RealDictCursor, connect_timeout=5)
    except (psycopg2.Error, sqlite3.Error) as exc:
        raise DatabaseUnavailable(f"could not connect to {BACKEND}") from exc


@contextmanager
def db_connection():
    """Yields a raw connection; rolls back on error and always closes. Callers commit explicitly."""
    conn = get_connection()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:  # connection may already be broken
            logger.debug("rollback failed", exc_info=True)
        raise
    finally:
        conn.close()


def _first_value(row):
    """First column of a row from either driver (psycopg2 dict rows or sqlite3 rows)."""
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


# ---------------------------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------------------------
def ensure_chunk_schema(conn) -> bool:
    """Create document_chunks + its dedup unique index. Returns whether the unique index is in place."""
    cur = conn.cursor()
    if BACKEND == "postgres":
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                chunk_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector({config.EMBEDDING_DIM})
            );
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                chunk_number INTEGER NOT NULL,
                content TEXT NOT NULL
            );
        """)
    conn.commit()
    try:
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_document_chunks_hash_chunk "
            "ON document_chunks (file_hash, chunk_number);"
        )
        conn.commit()
        return True
    except (psycopg2.Error, sqlite3.Error):
        conn.rollback()
        logger.error(
            "Could not create the dedup unique index: duplicate chunks already exist. "
            "Run `python -m backend.rag.ingest --rebuild` to rebuild the index from data/documents."
        )
        return False
    finally:
        cur.close()


def _migrate_history_table():
    """Lightweight additive migration (no Alembic yet): add columns introduced after the first release."""
    cols = {c["name"] for c in inspect(engine).get_columns("detection_history")}
    if "engine" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE detection_history ADD COLUMN engine VARCHAR(64)"))
        logger.info("Migrated detection_history: added column 'engine'")


def init_db():
    """Create/upgrade all tables. Raises DatabaseUnavailable if the database cannot be reached."""
    global DEDUP_CONSTRAINT_OK
    ensure_configured()
    try:
        Base.metadata.create_all(bind=engine)
        _migrate_history_table()
    except Exception as exc:
        raise DatabaseUnavailable("failed to initialise history table") from exc
    with db_connection() as conn:
        DEDUP_CONSTRAINT_OK = ensure_chunk_schema(conn)


# ---------------------------------------------------------------------------------------------
# Chunk queries shared by upload and batch ingestion
# ---------------------------------------------------------------------------------------------
def _ph() -> str:
    """SQL parameter placeholder for the active driver."""
    return "%s" if BACKEND == "postgres" else "?"


def find_document_by_hash(conn, file_hash: str) -> Optional[str]:
    """Source name of an already-indexed file with this content hash, or None."""
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT source FROM document_chunks WHERE file_hash = {_ph()} LIMIT 1;", (file_hash,))
        return _first_value(cur.fetchone())
    finally:
        cur.close()


def insert_chunks(conn, source: str, file_hash: str, chunks: Sequence[str],
                  embeddings: Optional[Sequence[Sequence[float]]]) -> int:
    """Insert chunks idempotently. Duplicate (file_hash, chunk_number) rows are skipped by the database,
    so concurrent uploads of the same content cannot create duplicates. Returns rows actually inserted.
    Does not commit."""
    cur = conn.cursor()
    inserted = 0
    try:
        for idx, chunk in enumerate(chunks, start=1):
            if BACKEND == "postgres":
                cur.execute(
                    "INSERT INTO document_chunks (source, file_hash, chunk_number, content, embedding) "
                    "VALUES (%s, %s, %s, %s, %s::vector) ON CONFLICT (file_hash, chunk_number) DO NOTHING;",
                    (source, file_hash, idx, chunk, str(list(embeddings[idx - 1]))),
                )
            else:
                cur.execute(
                    "INSERT OR IGNORE INTO document_chunks (source, file_hash, chunk_number, content) "
                    "VALUES (?, ?, ?, ?);",
                    (source, file_hash, idx, chunk),
                )
            inserted += max(cur.rowcount, 0)
        return inserted
    finally:
        cur.close()


def count_chunks(conn) -> Tuple[int, int]:
    """(total chunks, distinct documents) currently indexed."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) AS n, COUNT(DISTINCT file_hash) AS d FROM document_chunks;")
        row = cur.fetchone()
        return (row["n"], row["d"]) if isinstance(row, dict) else (row[0], row[1])
    finally:
        cur.close()
