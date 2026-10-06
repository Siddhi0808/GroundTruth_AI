"""B07/B10/B21: schema, idempotent inserts, concurrency dedup, connection cleanup, backend selection."""
import os
import sqlite3
import threading

import pytest

from backend import config, database


def _rows(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM document_chunks;")
    row = cur.fetchone()
    cur.close()
    return row["n"] if isinstance(row, dict) else row[0]


def _embs(n):
    return [[0.1] * config.EMBEDDING_DIM for _ in range(n)]


def test_dedup_unique_index_exists(db_backend):
    assert database.DEDUP_CONSTRAINT_OK is True


def test_insert_is_idempotent(db_backend):
    chunks = ["alpha chunk", "beta chunk"]
    with database.db_connection() as conn:
        first = database.insert_chunks(conn, "a.txt", "h1", chunks, _embs(2))
        conn.commit()
        second = database.insert_chunks(conn, "a.txt", "h1", chunks, _embs(2))
        conn.commit()
        assert (first, second) == (2, 0)
        assert _rows(conn) == 2
        assert database.find_document_by_hash(conn, "h1") == "a.txt"
        assert database.find_document_by_hash(conn, "nope") is None


def test_concurrent_inserts_of_same_document_do_not_duplicate(pg_backend):
    chunks = [f"chunk {i}" for i in range(20)]
    results, barrier = [], threading.Barrier(6)

    def worker():
        with database.db_connection() as conn:
            barrier.wait()
            results.append(database.insert_chunks(conn, "same.txt", "samehash", chunks, _embs(20)))
            conn.commit()

    threads = [threading.Thread(target=worker) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sum(results) == 20
    with database.db_connection() as conn:
        assert _rows(conn) == 20


def test_db_connection_rolls_back_and_closes_on_error(sqlite_backend):
    holder = {}
    with pytest.raises(RuntimeError):
        with database.db_connection() as conn:
            holder["conn"] = conn
            database.insert_chunks(conn, "x.txt", "hx", ["x"], None)
            raise RuntimeError("boom")
    with pytest.raises(sqlite3.ProgrammingError):  # closed
        holder["conn"].execute("SELECT 1")
    with database.db_connection() as conn:
        assert _rows(conn) == 0  # rolled back


def test_no_connection_leak_on_repeated_failures(pg_backend):
    def active():
        with database.db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS n FROM pg_stat_activity WHERE datname = current_database();")
            return cur.fetchone()["n"]

    before = active()
    for _ in range(15):
        with pytest.raises(Exception):
            with database.db_connection() as conn:
                conn.cursor().execute("SELECT * FROM table_that_does_not_exist;")
    assert active() <= before + 1


def test_history_migration_adds_engine_column(tmp_path):
    path = tmp_path / "legacy.db"
    legacy = sqlite3.connect(path)
    legacy.execute("CREATE TABLE detection_history (id INTEGER PRIMARY KEY, query TEXT NOT NULL, llm_response TEXT NOT NULL,"
                   " verdict VARCHAR(50) NOT NULL, confidence FLOAT NOT NULL, reason TEXT, created_at DATETIME)")
    legacy.execute("INSERT INTO detection_history (query, llm_response, verdict, confidence) VALUES ('q','r','Supported',90)")
    legacy.commit()
    legacy.close()
    database.configure_database(f"sqlite:///{path}", allow_fallback=False)
    database.init_db()
    cols = [r[1] for r in sqlite3.connect(path).execute("PRAGMA table_info(detection_history)")]
    assert "engine" in cols


def test_unreachable_postgres_fails_fast_without_fallback():
    with pytest.raises(database.DatabaseUnavailable):
        database.configure_database("postgresql://nobody@127.0.0.1:1/none", allow_fallback=False)


def test_postgres_scheme_alias_is_accepted(monkeypatch):
    """`postgres://` (Heroku-style) must not be mistaken for an unreachable database."""
    if not os.getenv("TEST_DATABASE_URL", "").startswith("postgresql://"):
        pytest.skip("TEST_DATABASE_URL (postgresql://...) not set; PostgreSQL tests skipped")
    database.configure_database(os.environ["TEST_DATABASE_URL"].replace("postgresql://", "postgres://", 1),
                                allow_fallback=False)
    assert database.database_status()["backend"] == "postgres"
    with database.db_connection() as conn:
        conn.cursor().execute("SELECT 1;")


def test_unreachable_postgres_falls_back_visibly_when_allowed(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SQLITE_PATH", str(tmp_path / "fallback.db"))
    database.configure_database("postgresql://nobody@127.0.0.1:1/none", allow_fallback=True)
    status = database.database_status()
    assert status["backend"] == "sqlite"
    assert status["fallback_active"] is True
    assert status["retrieval_mode"] == "keyword"
    assert status["fallback_reason"].startswith("postgres_unreachable")
