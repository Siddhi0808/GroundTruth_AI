"""API behaviour: detection, upload security/robustness, history/stats, and safe error handling."""
import io
import json
import threading

import pytest
from reportlab.pdfgen import canvas

from backend import config, database
import backend.main as main_mod
import backend.rag.ingest as ingest_mod
from backend.rag.embeddings import EmbeddingUnavailable


def _chunk_count():
    with database.db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM document_chunks;")
        row = cur.fetchone()
        return row["n"] if isinstance(row, dict) else row[0]


def _pdf_bytes(text):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


def _upload(client, name, data):
    return client.post("/api/upload", files={"file": (name, data)})


# ------------------------------------------------------------------------------------------ health
def test_health_reports_backend_and_llm(client, db_backend):
    body = client.get("/api/health").json()
    assert body["database"]["backend"] == db_backend
    assert body["database"]["reachable"] is True
    assert body["llm"]["enabled"] is False


# ------------------------------------------------------------------------------------------ detect
def test_detect_reports_actual_engine_and_saves_it(client, seeded):
    r = client.post("/detect", json={"query": "Who invented the telephone?",
                                     "llm_response": "Bell patented the telephone in 1876."})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "Supported"
    assert body["metadata"]["engine"] == "heuristic"
    assert body["metadata"]["model_used"] == config.HEURISTIC_ENGINE_NAME
    assert "Llama" not in json.dumps(body["metadata"])
    assert body["metadata"]["database_backend"] == seeded
    assert body["metadata"]["history_saved"] is True
    assert client.get("/api/history").json()[0]["engine"] == "heuristic"


def test_detect_with_llm_reports_llm_engine(client, seeded, fake_ollama):
    fake_ollama(json.dumps({"verdict": "Hallucinated", "confidence": 0.95, "reason": "The year is 1876."}))
    body = client.post("/detect", json={"query": "When was the telephone patented?",
                                        "llm_response": "In 1877."}).json()
    assert body["verdict"] == "Hallucinated"
    assert body["confidence"] == 95.0
    assert body["metadata"]["engine"] == "llm"
    assert body["metadata"]["model_used"].startswith("ollama:")
    assert client.get("/api/history").json()[0]["engine"] == "llm"


def test_detect_llm_down_is_explicit(client, seeded, fake_ollama):
    import requests
    fake_ollama(requests.ConnectionError("refused"))
    meta = client.post("/detect", json={"query": "Who invented the telephone?",
                                        "llm_response": "Bell patented the telephone in 1876."}).json()["metadata"]
    assert meta["engine"] == "heuristic"
    assert meta["fallback_reason"] == "llm_unavailable"
    assert meta["degraded"] is True


def test_empty_knowledge_base_gives_insufficient_evidence(client, db_backend):
    body = client.post("/detect", json={"query": "Who invented the telephone?",
                                        "llm_response": "Bell did."}).json()
    assert body["verdict"] == "Insufficient Evidence"
    assert body["metadata"]["engine"] == "none"


@pytest.mark.parametrize("payload", [
    {"llm_response": "Bell."},                                   # missing query
    {"query": "q", "llm_response": "Bell invented it."},          # too short
    {"query": "    ", "llm_response": "Bell invented it."},      # whitespace only
    {"query": "Who?", "llm_response": "Bell.", "top_k": 0},
    {"query": "Who?", "llm_response": "Bell.", "top_k": 11},
    {"query": 123, "llm_response": ["not", "a", "string"]},
])
def test_invalid_detect_requests_are_422(client, db_backend, payload):
    assert client.post("/detect", json=payload).status_code == 422


def test_malformed_json_is_422(client, db_backend):
    r = client.post("/detect", content=b"{not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


def test_retrieval_failure_is_503_not_a_verdict(client, seeded, monkeypatch):
    def broken():
        raise database.DatabaseUnavailable("password authentication failed for user SECRET_USER")
    monkeypatch.setattr(database, "get_connection", broken)
    r = client.post("/detect", json={"query": "Who invented the telephone?", "llm_response": "Bell."})
    assert r.status_code == 503
    assert r.json()["detail"]["error"] == "retrieval_unavailable"
    assert "SECRET_USER" not in r.text
    assert "verdict" not in r.json()


def test_unexpected_error_is_generic_500_without_internals(client, seeded, monkeypatch):
    def explode(*a, **k):
        raise RuntimeError("internal detail SECRET_TOKEN at /srv/app/judge.py")
    monkeypatch.setattr(main_mod, "evaluate_hallucination", explode)
    r = client.post("/detect", json={"query": "Who invented the telephone?", "llm_response": "Bell."})
    assert r.status_code == 500
    assert r.json()["detail"]["error"] == "internal_error"
    assert r.json()["detail"]["error_id"]
    assert "SECRET_TOKEN" not in r.text and "judge.py" not in r.text


def test_history_write_failure_is_reported_not_hidden(client, seeded, monkeypatch):
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Session

    def fail(self):
        raise OperationalError("INSERT", {}, Exception("disk full"))
    monkeypatch.setattr(Session, "commit", fail)
    r = client.post("/detect", json={"query": "Who invented the telephone?",
                                     "llm_response": "Bell patented the telephone in 1876."})
    assert r.status_code == 200
    assert r.json()["metadata"]["history_saved"] is False


# ------------------------------------------------------------------------------------------ upload
def test_upload_txt_indexes_and_stores_safely(client, db_backend):
    r = _upload(client, "notes.txt", b"The Eiffel Tower was completed in 1889 in Paris.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success" and body["chunks_ingested"] == 1
    stored = config.DOCUMENTS_DIR / body["filename"]
    assert stored.exists() and body["filename"].endswith("_notes.txt")
    assert list(config.DOCUMENTS_DIR.glob(".*.uploading")) == []


def test_upload_pdf(client, db_backend):
    r = _upload(client, "doc.pdf", _pdf_bytes("Graphene is a single layer of carbon atoms."))
    assert r.status_code == 200, r.text
    assert r.json()["chunks_ingested"] == 1


def test_duplicate_upload_creates_no_new_chunks(client, db_backend):
    data = b"Venus has a retrograde rotation and a very long sidereal day."
    first = _upload(client, "venus.txt", data).json()
    before = _chunk_count()
    second = _upload(client, "venus.txt", data).json()
    renamed = _upload(client, "other-name.txt", data).json()
    assert first["status"] == "success"
    assert second["status"] == "duplicate" and renamed["status"] == "duplicate"
    assert _chunk_count() == before
    assert len([p for p in config.DOCUMENTS_DIR.iterdir() if not p.name.startswith(".")]) == 1


def test_concurrent_duplicate_uploads(client, pg_backend):
    data = ("Tardigrades survive extreme conditions. " * 40).encode()
    statuses, barrier = [], threading.Barrier(5)

    def go():
        barrier.wait()
        statuses.append(_upload(client, "tardigrade.txt", data).json()["status"])

    threads = [threading.Thread(target=go) for _ in range(5)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert statuses.count("success") == 1 and statuses.count("duplicate") == 4
    with database.db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n, COUNT(DISTINCT chunk_number) AS d FROM document_chunks;")
        row = cur.fetchone()
    assert row["n"] == row["d"]  # no duplicated (file_hash, chunk_number)
    assert list(config.DOCUMENTS_DIR.glob(".*.uploading")) == []  # losers clean up their temp files
    assert len(list(config.DOCUMENTS_DIR.iterdir())) == 1


def test_race_loser_path_cleans_up_temp_file(client, db_backend, monkeypatch):
    """Force the `inserted == 0` branch (another request committed the same content first)."""
    monkeypatch.setattr(main_mod, "index_document", lambda *a, **k: 0)
    r = _upload(client, "race.txt", b"Content that another request already indexed.")
    assert r.json()["status"] == "duplicate"
    assert list(config.DOCUMENTS_DIR.iterdir()) == []


@pytest.mark.parametrize("evil", ["../../evil.txt", "/etc/evil.txt", "..\\..\\evil.txt", "sub/../../evil.txt"])
def test_path_traversal_filenames_stay_inside_documents_dir(client, db_backend, evil):
    r = _upload(client, evil, b"Harmless content about the telephone patent of 1876.")
    assert r.status_code == 200, r.text
    name = r.json()["filename"]
    assert "/" not in name and "\\" not in name and ".." not in name
    assert (config.DOCUMENTS_DIR / name).resolve().parent == config.DOCUMENTS_DIR.resolve()
    assert not (config.DOCUMENTS_DIR.parent / "evil.txt").exists()
    assert not (config.DOCUMENTS_DIR.parent.parent / "evil.txt").exists()


@pytest.mark.parametrize("name, data, code", [
    ("notes.docx", b"PK\x03\x04", "unsupported_file_type"),
    ("empty.txt", b"", "empty_file"),
    ("latin1.txt", "Café crème".encode("latin-1"), "invalid_document"),
    ("binary.txt", b"abc\x00\x01\x02", "invalid_document"),
    ("fake.pdf", b"this is not a pdf", "invalid_document"),
    ("corrupt.pdf", b"%PDF-1.4\n garbage without objects", "invalid_document"),
])
def test_bad_uploads_are_400_with_safe_message(client, db_backend, name, data, code):
    r = _upload(client, name, data)
    assert r.status_code == 400
    assert r.json()["detail"]["error"] in (code, "no_text")
    assert _chunk_count() == 0
    assert list(config.DOCUMENTS_DIR.iterdir()) == []


def test_database_failure_during_insert_leaves_no_file_and_no_rows(client, db_backend, monkeypatch):
    def fail(*a, **k):
        raise RuntimeError("constraint exploded: SECRET_SQL")
    monkeypatch.setattr(main_mod, "index_document", fail)
    r = _upload(client, "fact.txt", b"The Dead Sea is about 430 meters below sea level.")
    assert r.status_code == 500
    assert r.json()["detail"]["error"] == "upload_failed"
    assert "SECRET_SQL" not in r.text
    assert list(config.DOCUMENTS_DIR.iterdir()) == []
    assert _chunk_count() == 0


def test_embedding_failure_is_503(client, pg_backend, monkeypatch):
    def fail(_chunks):
        raise EmbeddingUnavailable("model gone")
    monkeypatch.setattr(ingest_mod, "get_embeddings", fail)
    r = _upload(client, "fact.txt", b"Olympus Mons is the tallest volcano in the Solar System.")
    assert r.status_code == 503
    assert list(config.DOCUMENTS_DIR.iterdir()) == []


# ------------------------------------------------------------------------------------------ history / stats
def test_history_returns_raw_text_and_limit_is_bounded(client, seeded):
    payload = "<img src=x onerror=alert(1)>"
    client.post("/detect", json={"query": payload, "llm_response": "Bell patented the telephone in 1876."})
    item = client.get("/api/history").json()[0]
    assert item["query"] == payload  # API returns data; the frontend must render it as text (see test_frontend_security)
    assert client.get("/api/history?limit=1000").status_code == 422


def test_stats_counts_all_verdicts(client, seeded):
    client.post("/detect", json={"query": "Who invented the telephone?", "llm_response": "Bell patented the telephone in 1876."})
    client.post("/detect", json={"query": "Who invented the telephone?", "llm_response": "Bell patented the telephone in 1877."})
    client.post("/detect", json={"query": "Who invented the telephone?", "llm_response": "ok ok"})
    s = client.get("/api/stats").json()
    assert (s["total_evaluations"], s["supported_count"], s["hallucinated_count"], s["insufficient_evidence_count"]) == (3, 1, 1, 1)
    assert s["hallucination_rate"] == pytest.approx(33.33)


def test_stats_and_history_db_failure_is_503(client, seeded, monkeypatch):
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Query

    def fail(self, *a, **k):
        raise OperationalError("SELECT", {}, Exception("connection refused SECRET_HOST"))
    monkeypatch.setattr(Query, "all", fail)
    for path in ("/api/stats", "/api/history"):
        r = client.get(path)
        assert r.status_code == 503 and "SECRET_HOST" not in r.text
