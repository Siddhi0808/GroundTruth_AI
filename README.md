# 🛡️ GroundTruth AI

**A RAG-based hallucination-detection service for LLM answers.**

GroundTruth AI checks an LLM's answer against a document knowledge base. It retrieves the most relevant passages for the question and a judge labels the answer **Supported**, **Hallucinated**, or **Insufficient Evidence**, with a confidence value, a reason, the evidence passages, and which engine made the decision.

> This README describes the current code. Earlier versions of this README reported 89.30% accuracy / 92.27% F1; those numbers came from the rule-based fallback judge on a synthetic dev set that the rules had been tuned on, most likely using SQLite keyword retrieval. See [Evaluation](#evaluation) for current, reproducible results, including a held-out set.

---

## Contents
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Setup](#setup)
- [Configuration](#configuration)
- [API](#api)
- [Evaluation](#evaluation)
- [Testing](#testing)
- [Known limitations](#known-limitations)
- [Project structure](#project-structure)

---

## How it works

```
Browser (vanilla JS) ──POST /detect──▶ FastAPI (backend/main.py)
                                         │
                   retrieve_context()    ▼
        SentenceTransformers all-MiniLM-L6-v2 (384-d, normalised)
                                         │
     PostgreSQL + pgvector: ORDER BY embedding <=> query LIMIT k   (primary, vector search)
     SQLite + keyword-stem overlap                                   (degraded fallback, reported)
                                         │  top-k evidence chunks
                                         ▼
     Judge (backend/llm/judge.py)
       1. Ollama llama3.2 (temperature 0, seed 42, JSON output validated with Pydantic)
       2. Deterministic rule engine if the LLM is disabled, unavailable, or returns invalid output
                                         │
                                         ▼
     JSON: verdict, confidence, reason, evidence, metadata.engine / model_used / fallback_reason
     + row in detection_history (including the engine)
```

- **Verdicts.** `Supported`, `Hallucinated`, or `Insufficient Evidence`, used when no evidence is retrieved or the judge cannot decide. Infrastructure failures are **not** verdicts: they return HTTP 503.
- **Ingestion.** `.txt`/`.pdf` files are parsed with pypdf, with an OCR fallback on upload. They're hashed with SHA-256 of the raw bytes, which is the dedup key. Text is split into **≤200-token chunks with 40-token overlap**, measured with the embedding model's own tokenizer (the model truncates at 256), embedded in batches, and inserted with a `UNIQUE (file_hash, chunk_number)` constraint.
- **Graceful degradation, made visible.** If Postgres is unreachable *at startup* and `ALLOW_SQLITE_FALLBACK=true`, the app runs on SQLite with keyword retrieval. This is logged at ERROR level and reported by `/api/health` and every `/detect` response. The backend is never switched mid-run. If the chosen database fails later, requests get 503.

## Tech stack
| Layer | Used for |
|---|---|
| FastAPI, Uvicorn, Pydantic v2 | API, validation, OpenAPI docs at `/docs`, static frontend |
| PostgreSQL + pgvector | chunk storage and cosine-distance search (`<=>`), exact scan (no ANN index yet) |
| SQLite | optional degraded fallback (keyword retrieval, no vectors) |
| SQLAlchemy 2 / psycopg2 | ORM for history; raw SQL for vector queries |
| SentenceTransformers `all-MiniLM-L6-v2` | 384-d embeddings |
| langchain-text-splitters | recursive splitter measured in model tokens |
| Ollama `llama3.2` (3.2B, Q4_K_M) | LLM judge |
| pypdf, pdf2image + pytesseract | PDF text, OCR fallback on upload |
| Vanilla HTML/CSS/JS | UI (all dynamic text rendered with `textContent`) |
| pytest, GitHub Actions (pgvector service) | tests / CI |
| Docker, Docker Compose | container + pgvector database |

## Setup

Prerequisites: Python 3.12+ (the pinned scipy needs it), PostgreSQL 14+ with the [pgvector](https://github.com/pgvector/pgvector) extension, optionally [Ollama](https://ollama.com), and optionally `poppler-utils` + `tesseract-ocr` for OCR.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env            # then edit DATABASE_URL
createdb groundtruth
ollama pull llama3.2            # optional; without it the rule engine judges
python -m backend.rag.ingest    # index data/documents (use --rebuild after changing chunking)
uvicorn backend.main:app --port 8000
```
Open `http://localhost:8000` (detector), `/dashboard`, `/history`, `/docs`.

**Docker Compose:** `docker compose up --build` starts pgvector and the app. The app reaches the database at `db` via `DATABASE_URL`, and Ollama on the host via `OLLAMA_URL=http://host.docker.internal:11434`. `ALLOW_SQLITE_FALLBACK=false` means a missing database stops the container instead of silently degrading.

```bash
docker compose up -d --build                                  # Postgres (host port 5433) + app (port 8000)
docker compose exec app python -m backend.rag.ingest          # index data/documents into the container DB
curl localhost:8000/api/health                                # expect "healthy", backend "postgres"
docker compose down                                           # stop (add -v to delete the DB volume)
```
The image uses Python 3.13 and CPU-only PyTorch (image ≈ 570 MB). Ollama is not containerised: run it on the host with `llama3.2` pulled. Verified on 2026-09-27 (Docker Desktop, Apple M4): health `healthy` on Postgres with the LLM reachable; ingestion produced the same 1,904 chunks as a local run (≈ 5 min on CPU); `/detect` returned an LLM verdict with the same retrieval scores as local; upload and duplicate upload behaved as expected.

## Configuration
All settings live in `backend/config.py`, read from the environment or a project-root `.env` (real environment variables win). See `.env.example`.

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | built from `POSTGRES_*` | PostgreSQL URL (or `sqlite:///path`) |
| `ALLOW_SQLITE_FALLBACK` | `true` | on Postgres failure at startup: degrade to SQLite (true) or refuse to start (false) |
| `USE_LLM` | `true` | `false` = always use the rule engine |
| `OLLAMA_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `llama3.2` | LLM endpoint and model |
| `OLLAMA_TIMEOUT_SECONDS` | `35` | per-request timeout |
| `LLM_TEMPERATURE` / `LLM_SEED` / `LLM_NUM_CTX` | `0` / `42` / `4096` | deterministic decoding for the judge |
| `CHUNK_SIZE_TOKENS` / `CHUNK_OVERLAP_TOKENS` | `200` / `40` | must stay below the model's 254-token content limit |

Temperature 0 with a fixed seed makes judgements much more repeatable, which matters for benchmarking. It does not guarantee identical output across Ollama versions, model builds, or hardware.

## API
| Endpoint | Method | Notes |
|---|---|---|
| `/detect`, `/api/detect` | POST | body `{query, llm_response, top_k?}`. `query`/`llm_response` are stripped and must be ≥ 2 chars; `top_k` is 1–10 (default 3). 200 returns a verdict; 422 on invalid input; 503 if retrieval is unavailable; 500 on unexpected errors. |
| `/api/upload` | POST | multipart `file` (.txt / .pdf). Returns `status: success` or `duplicate`. 400 on unsupported/empty/unreadable files; 503 if the index is unavailable; 500 otherwise. |
| `/api/history?limit=` | GET | recent detections (1 ≤ limit ≤ 100), including `engine`; 503 on DB failure |
| `/api/stats` | GET | totals per verdict and hallucination rate; 503 on DB failure |
| `/api/health` | GET | `healthy` / `degraded`, DB backend, fallback state, DB and Ollama reachability |

Example `/detect` metadata:
```json
{"top_k_requested": 3, "evidence_count": 3, "engine": "llm", "model_used": "ollama:llama3.2",
 "fallback_reason": null, "database_backend": "postgres", "retrieval_mode": "vector",
 "degraded": false, "history_saved": true}
```
`engine` is `llm`, `heuristic` (with `fallback_reason`: `llm_disabled`, `llm_unavailable`, or `llm_invalid_output`), or `none` (no evidence). Error bodies are `{"detail": {"error": <code>, "message": <safe text>, "error_id"?: <id>}}`. Stack traces and driver messages go to the server log only.

**Not implemented:** authentication, rate limiting, upload size/page limits, API versioning. Treat this as a local/demo service.

## Evaluation

Run with `python -m benchmarks.run_benchmark --dataset <file> --engine heuristic|llm [--dedupe] [--sample N]`. Every result file in `benchmarks/results/` stores its full configuration: engine, model and options, database backend and retrieval mode, embedding model, chunking, top_k, dataset SHA-256, case counts, git commit, and latency.

**Datasets**
- `dev_v1_1000.json`: 1,000 synthetic cases from `scripts/generate_1000_benchmark.py` (300 Supported, 200 inversions, 200 entity swaps, 150 numeric perturbations, 150 out-of-corpus). **Only 834 unique** query/response pairs, heavily templated. The rule engine was developed against this set, so treat it as a **development set**.
- `heldout_v1.json`: 150 hand-written cases (40 / 30 / 25 / 25 / 30) from facts in the long_* documents, with phrasings independent of the dev generator. It was written *before* the rule changes were evaluated on it, and run **once**. It is still synthetic and was authored by the same development process (an AI assistant), so it is a sanity check on generalisation, not an independent benchmark.

**Scoring.** Positive class = *not supported* (`Hallucinated` or `Insufficient Evidence`), since both mean "don't trust this answer". A 3-way accuracy is also reported.

**Results** (PostgreSQL + pgvector, top_k = 3, 200/40-token chunks, 1,904 chunks from 409 documents, 2026-09-26/27)

| Engine | Set | n | Accuracy | Not-supported P / R / F1 | Supported P / R / F1 | Macro-F1 |
|---|---|---|---|---|---|---|
| Rules v2 | dev (all) | 1000 | 90.8 | 90.2 / 97.4 / 93.7 | 92.6 / 75.3 / 83.1 | 88.4 |
| Rules v2 | dev (deduplicated) | 834 | 94.6 | — | — | 89.7 |
| Rules v2 | **held-out** | 150 | **72.0** | 92.5 / 67.3 / 77.9 | 48.6 / 85.0 / 61.8 | **69.9** |
| Llama 3.2 3B (Ollama, temp 0) | **held-out** | 150 | **72.7** | 100.0 / 62.7 / 77.1 | 49.4 / 100.0 / 66.1 | **71.6** |
| Llama 3.2 3B (Ollama, temp 0) | dev (stratified sample of 200 unique cases, seed 7) | 200 | 89.5 | 100.0 / 87.5 / 93.3 | 60.4 / 100.0 / 75.3 | 84.3 |
| Rules v2 on the same 200 dev cases | dev sample | 200 | 95.5 | 96.5 / 98.2 / 97.4 | 89.7 / 81.3 / 85.3 | 91.3 |
| Rules v2, SQLite keyword mode | dev / held-out | 1000 / 150 | 84.6 / 74.0 | — | — | 78.9 / 71.4 |

What this shows:
- **The rules don't generalise.** 90.8% on dev vs 72.0% on held-out. Negation/inversion accuracy drops from 94% (dev) to 27% (held-out), because the rules recognise the dev generator's phrasings. The held-out majority-class baseline is 73.3%, so the rule engine is **not better than always answering "not supported"** there.
- Numeric perturbations (88–100%) and out-of-corpus questions (100%) are the rules' reliable signals.
- **The LLM judge doesn't stay grounded.** On held-out it never rejected a correct answer (Supported recall 100%) and caught most inversions (83%) and entity swaps (88%). But it called **26 of 30 out-of-corpus facts "Supported"** (13% correct on that category), using its own world knowledge instead of the retrieved evidence. There were zero LLM fallbacks in the run; latency p50 15.2 s, p95 19.2 s on an Apple M4.
- On the dev sample, the LLM rejects 100% of out-of-corpus cases. Those dev cases describe fictional or implausible facts, while the held-out ones are well-known *true* facts. So the LLM effectively judges by its own beliefs, not by the retrieved evidence. (The dev-sample run had 1 LLM timeout, which fell back to the rules and is counted in the result metadata.)
- The two engines fail in opposite places (rules: inversions 27%, swaps 56%; LLM: out-of-corpus 13%, numbers 72%). A cascade is the obvious next experiment, but it must be designed on the dev set and confirmed on a *new* held-out set.
- With n = 150, a 95% confidence interval on held-out accuracy is roughly ±7 points.

Legacy results (`benchmarks/legacy/`) are kept for reference only. They were produced by the pre-fix code and are not comparable.

## Testing
```bash
TEST_DATABASE_URL=postgresql:///groundtruth_test python -m pytest -q    # PostgreSQL tests are skipped if unset
```
154 tests (152 pass; 2 are backend-specific checks that are skipped by design; many tests run on both SQLite and PostgreSQL). The suite covers chunk token limits and overlap; each rule of the deterministic judge, including the audit's false positives; LLM output validation (malformed, extra text, missing, null, or unexpected labels, out-of-range values) with a mocked Ollama; fallback reporting; retrieval on both backends; infrastructure failures (503, no silent `[]`); every endpoint's validation and error bodies (no leaked internals); upload path traversal, dedup (sequential and concurrent), and cleanup on failure; history/stats; the history-table migration; the config / Compose / `.env` contract; and a static XSS check on the frontend. CI (GitHub Actions) runs everything against a pgvector service and passes; Ollama is never required. Test fixtures force a throwaway `DATABASE_URL`, so tests can never touch a real database.

Manually verified on 2026-09-26: the full UI flow (detect with the live LLM, upload, duplicate upload, history, dashboard) against local Postgres and Ollama, plus a stored-XSS payload rendering as text in `/history`.

## Known limitations
- The rule engine is brittle and overfit to the dev set (see Evaluation). Its confidences are fixed per rule, not calibrated probabilities.
- The LLM judge can itself hallucinate, e.g. calling an out-of-corpus claim "Supported" and citing context that doesn't contain it. Its self-reported confidence is uncalibrated. It is also slow on a laptop (~12–20 s/request warm; the first load of the model can take minutes).
- Retrieval embeds only the **query**, not the response, and has no relevance threshold: top-k chunks are always returned when the index is non-empty.
- The binary label set can't separate "false" from "true but not in the knowledge base". `Insufficient Evidence` helps only when nothing is retrieved or the rules are undecided.
- **Corpus quality:** of 410 files, about 70 are template filler with no facts, most `long_*` "treatises" are ~75% repeated template sentences, one PDF has no extractable text, and one is a `test.txt` stub.
- No auth, rate limiting, or upload size limits; CORS allows all origins; no Alembic migrations (one additive migration runs in code); exact (non-ANN) vector search; one model instance serialises embedding calls.

## Project structure
```
backend/
  config.py          environment contract (.env supported)
  database.py        backend selection, schema, connections, idempotent chunk inserts
  main.py            FastAPI app, endpoints, error handling, upload flow
  rag/  chunker.py (token-aware) · document_loader.py (parse/validate/hash) · embeddings.py
        ingest.py (batch + shared indexing, --rebuild) · retriever.py (vector / keyword)
  llm/  judge.py (Ollama judge + rules v2)
frontend/            index.html, dashboard.html, history.html, script.js, style.css
benchmarks/          run_benchmark.py, metrics.py, datasets/, results/, legacy/ (old result files only)
scripts/             corpus and dev-set generators
tests/               pytest suite
```

## License
MIT
