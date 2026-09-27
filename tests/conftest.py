"""Shared fixtures. Tests never touch the real database or data/documents:
- SQLite tests use a temporary file.
- PostgreSQL tests use TEST_DATABASE_URL (skipped if unset) and truncate their tables before each test.
- The LLM is never called for real; tests that need it mock `requests.post`.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("USE_LLM", "false")
os.environ.setdefault("ALLOW_SQLITE_FALLBACK", "false")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest  # noqa: E402

from backend import config, database  # noqa: E402

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def _truncate(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM document_chunks;")
    cur.execute("DELETE FROM detection_history;")
    cur.close()
    conn.commit()


@pytest.fixture(params=["sqlite", "postgres"])
def db_backend(request, tmp_path, monkeypatch):
    """Parametrised over both backends; yields the backend name with a clean, initialised database."""
    if request.param == "sqlite":
        database.configure_database(f"sqlite:///{tmp_path / 'test.db'}", allow_fallback=False)
    else:
        if not TEST_DATABASE_URL:
            pytest.skip("TEST_DATABASE_URL not set; PostgreSQL tests skipped")
        database.configure_database(TEST_DATABASE_URL, allow_fallback=False)
    database.init_db()
    with database.db_connection() as conn:
        _truncate(conn)
    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setattr(config, "DOCUMENTS_DIR", docs)
    yield request.param


@pytest.fixture
def sqlite_backend(tmp_path, monkeypatch):
    database.configure_database(f"sqlite:///{tmp_path / 'test.db'}", allow_fallback=False)
    database.init_db()
    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setattr(config, "DOCUMENTS_DIR", docs)
    return "sqlite"


@pytest.fixture
def pg_backend(tmp_path, monkeypatch):
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set; PostgreSQL tests skipped")
    database.configure_database(TEST_DATABASE_URL, allow_fallback=False)
    database.init_db()
    with database.db_connection() as conn:
        _truncate(conn)
    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setattr(config, "DOCUMENTS_DIR", docs)
    return "postgres"


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


SAMPLE_DOCS = {
    "telephone.txt": "Alexander Graham Bell was a Scottish-born inventor. He invented the first practical telephone. "
                     "Bell received a patent for the telephone in 1876.",
    "penicillin.txt": "Penicillin was discovered by Alexander Fleming in September 1928 at St. Mary's Hospital in London. "
                      "A mold called Penicillium notatum inhibited the growth of Staphylococcus bacteria.",
    "venus.txt": "Venus rotates in the opposite direction to most planets, which is called retrograde rotation. "
                 "A sidereal day on Venus lasts approximately 243 Earth days.",
}


@pytest.fixture
def seeded(db_backend):
    """Index SAMPLE_DOCS into the current test database via the real ingestion pipeline."""
    from backend.rag.ingest import ingest
    for name, text in SAMPLE_DOCS.items():
        (config.DOCUMENTS_DIR / name).write_text(text, encoding="utf-8")
    ingest(folder=config.DOCUMENTS_DIR)
    return db_backend


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


@pytest.fixture
def fake_ollama(monkeypatch):
    """Replace requests.post in the judge with a stub. Call with the raw model text, an int status,
    or an exception instance. Returns the list of captured calls."""
    import backend.llm.judge as judge_mod
    calls = []

    def install(behaviour):
        def fake_post(url, json=None, timeout=None):
            calls.append({"url": url, "json": json, "timeout": timeout})
            if isinstance(behaviour, Exception):
                raise behaviour
            if isinstance(behaviour, int):
                return FakeResponse(status_code=behaviour, text="error")
            return FakeResponse(payload={"response": behaviour})
        monkeypatch.setattr(judge_mod.requests, "post", fake_post)
        monkeypatch.setattr(config, "USE_LLM", True)
        return calls
    return install
