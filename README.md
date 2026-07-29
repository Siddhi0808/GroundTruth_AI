# 🛡️ GroundTruth AI

**A RAG-Based LLM Hallucination Detection & Context Verification Engine**

GroundTruth AI inspects a Large Language Model's response against a verified, embedded knowledge base and issues a **Supported** or **Hallucinated** verdict — complete with a confidence score, a natural-language explanation, and the exact evidence passages used to reach that decision.

---

## Table of Contents

- [Overview & Motivation](#overview--motivation)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture & Workflow](#architecture--workflow)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Roadmap](#roadmap)

---

## Overview & Motivation

Large Language Models are fluent but not always factual. They can generate plausible-sounding claims that have no basis in reality — a failure mode commonly known as **hallucination**. This is a critical problem for any production system where trust and accuracy matter: customer support bots, internal knowledge assistants, research tools, and RAG pipelines built on top of LLMs.

**GroundTruth AI** addresses this problem directly by acting as an independent verification layer that sits *after* an LLM has generated a response:

1. A user submits the original **query** and the **LLM-generated response** they want to fact-check.
2. GroundTruth AI performs a **vector similarity search** over a corpus of embedded, trusted source documents (PDF/TXT) to retrieve the most relevant ground-truth passages.
3. A **judge model** (a locally-hosted LLM, with a deterministic rule-based fallback) compares the response against the retrieved evidence and renders a verdict, a confidence score, and a step-by-step justification.
4. The result — including full evidence provenance — is returned as JSON and rendered in a real-time dashboard UI.

In short: instead of trusting an LLM's output blindly, GroundTruth AI **grounds it in retrievable evidence** and tells you exactly how confident you should be.

---

## Key Features

- **Unified FastAPI Server** — A single FastAPI application serves both the REST API and the static frontend (HTML/CSS/JS) from one process on port `8000`. No separate frontend server or build step required.

- **Dynamic Knowledge Base Ingestion** — Upload `.txt` or `.pdf` documents directly through the UI (`POST /api/upload`). Each file is:
  - Text-extracted (with an OCR fallback via `pdf2image` + `pytesseract` for scanned/image-based PDFs),
  - Persisted to disk in `data/documents/`,
  - Hashed with **MD5** for change tracking,
  - Split into numbered chunks,
  - Embedded and written into the vector store — all in one pipeline call.

- **Vector Search Pipeline** — Query and document chunks are embedded using **SentenceTransformers (`all-MiniLM-L6-v2`)** and matched using **cosine similarity** via **PostgreSQL + `pgvector`**, returning the top-*k* most relevant evidence passages for any query.

- **Dual-Engine LLM Judge** — The verdict engine first attempts to reason over the query, response, and retrieved context using a **locally-hosted Llama 3.2 model via Ollama**, prompted to return structured JSON (`verdict`, `confidence`, `reason`). If Ollama is unreachable or fails, the system automatically falls back to a **deterministic, rule-based heuristic judge** so the API never goes down — offering graceful degradation instead of a hard failure.

- **Real-Time UI & Dashboard** — A dark-themed, dependency-free frontend featuring:
  - A live **pipeline status tracker** (Context Retrieval → Claim Verification → Verdict Judgment),
  - A color-coded **verdict banner** (Supported vs. Hallucinated),
  - A visual **confidence gauge / progress bar**,
  - **Evidence provenance cards** showing the exact source document, chunk content, and similarity score behind each verdict,
  - A dedicated **Analytics Dashboard** (`/dashboard`) with aggregate hallucination-rate telemetry,
  - A full **History** view (`/history`) of past evaluations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, Uvicorn, Pydantic, Python-Multipart, SQLAlchemy |
| **AI / RAG** | SentenceTransformers (`all-MiniLM-L6-v2`), LangChain Text Splitters, Ollama (Llama 3.2), pypdf, pdf2image + pytesseract (OCR fallback), NumPy, PyTorch, Transformers |
| **Database** | PostgreSQL + `pgvector` (primary vector store), psycopg2-binary, SQLite (automatic local fallback when Postgres is unreachable) |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (no framework/build step) served natively via FastAPI's `StaticFiles` |

> Full dependency list available in [`requirements.txt`](./requirements.txt).

---

## Architecture & Workflow

```
                         ┌───────────────────────────┐
                         │   User Request / Upload    │
                         │  (Query + LLM Response,    │
                         │   or PDF/TXT document)      │
                         └─────────────┬───────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │        FastAPI Server       │
                         │  (main.py — single process, │
                         │   serves API + static UI)   │
                         └─────────────┬───────────────┘
                                       │
                       ┌───────────────┴────────────────┐
                       ▼                                 ▼
        ┌───────────────────────────┐      ┌───────────────────────────┐
        │  Ingestion Pipeline         │      │  Retrieval Pipeline         │
        │  (chunking + MD5 hashing)   │      │  (query embedding)          │
        └─────────────┬───────────────┘      └─────────────┬───────────────┘
                       │                                     │
                       ▼                                     ▼
        ┌─────────────────────────────────────────────────────────────┐
        │      SentenceTransformers (all-MiniLM-L6-v2) Embeddings       │
        │      +  PostgreSQL / pgvector  (cosine similarity search)     │
        └─────────────────────────────┬───────────────────────────────┘
                                       │  top-k evidence chunks
                                       ▼
                         ┌───────────────────────────┐
                         │        LLM Judge Engine     │
                         │  Ollama (Llama 3.2) primary │
                         │  Rule-based fallback         │
                         │  → verdict / confidence /    │
                         │    reasoning                  │
                         └─────────────┬───────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │     JSON Response / UI       │
                         │  Verdict badge, confidence    │
                         │  gauge, evidence cards,       │
                         │  saved to detection_history   │
                         └───────────────────────────┘
```

**Flow summary:**
`[User Request/Upload]` → `[FastAPI]` → `[SentenceTransformers / pgvector]` → `[LLM Judge]` → `[JSON / UI Render]`

---

## Project Structure

```
groundtruth-ai/
├── backend/
│   ├── main.py                 # FastAPI app, routes, request/response schemas
│   ├── database.py             # SQLAlchemy engine, DetectionHistory model, Postgres/SQLite fallback
│   ├── config.py
│   ├── rag/
│   │   ├── embeddings.py       # SentenceTransformer ('all-MiniLM-L6-v2') embedding generation
│   │   ├── retriever.py        # pgvector cosine-similarity retrieval logic
│   │   ├── chunker.py          # LangChain RecursiveCharacterTextSplitter wrapper
│   │   ├── ingest.py           # Batch ingestion script for data/documents/
│   │   ├── document_loader.py  # PDF/TXT loading utilities
│   │   └── store_embeddings.py # Example single-document embedding script
│   └── llm/
│       ├── judge.py            # Dual-engine hallucination judge (Ollama + heuristic fallback)
│       └── claim_extractor.py  # Ollama-based factual claim extraction utility
├── frontend/
│   ├── index.html              # Main detector UI
│   ├── dashboard.html          # Analytics dashboard
│   ├── history.html            # Evaluation history view
│   ├── script.js               # Detector page logic
│   ├── dashboard.js            # Dashboard stats logic
│   └── style.css               # Dark-themed styling
├── data/
│   └── documents/               # Ground-truth source documents (PDF/TXT corpus)
└── requirements.txt
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with the [`pgvector`](https://github.com/pgvector/pgvector) extension
- [Ollama](https://ollama.com) (for the local Llama 3.2 judge model) — optional but recommended
- `poppler-utils` and `tesseract-ocr` (system packages, only required for the scanned-PDF OCR fallback)

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/groundtruth-ai.git
cd groundtruth-ai
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

> If your dependency file lives at the project root instead, use `pip install -r requirements.txt`.

### 4. Configure PostgreSQL + pgvector

Create the database and enable the vector extension:

```bash
createdb groundtruth
psql -d groundtruth -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Create a `.env` file inside `backend/` with your connection details:

```env
POSTGRES_DB=groundtruth
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

> **No Postgres available?** No problem — `backend/database.py` automatically detects a failed connection at startup and transparently falls back to a local SQLite database (`groundtruth_fallback.db`) so the app still runs (vector similarity search will be limited to recency-based ordering in this mode).

### 5. Pull and Run the Local LLM Judge (Ollama)

```bash
ollama pull llama3.2
ollama serve
```

Ollama should be reachable at `http://localhost:11434`. If it isn't running, `judge.py` automatically falls back to the deterministic rule-based heuristic engine — the `/detect` endpoint will still return a verdict.

### 6. Ingest the Initial Knowledge Base (optional)

To bulk-embed everything already sitting in `data/documents/`:

```bash
python -m backend.rag.ingest
```

---

## Running the Application

Start the unified FastAPI server (serves both the API and the frontend on the same port):

```bash
uvicorn backend.main:app --reload
```

Then open:

| URL | Description |
|---|---|
| `http://localhost:8000/` | Detector UI |
| `http://localhost:8000/dashboard` | Analytics Dashboard |
| `http://localhost:8000/history` | Evaluation History |
| `http://localhost:8000/docs` | Interactive Swagger API Docs |

---

## API Reference

All endpoints are defined in [`backend/main.py`](./backend/main.py).

### `POST /detect` *(alias: `POST /api/detect`)*

Runs the full hallucination-detection pipeline: retrieves evidence, invokes the LLM judge, persists the result to history, and returns the verdict.

**Request Body**

```json
{
  "query": "Who invented the telephone?",
  "llm_response": "Thomas Edison invented the telephone.",
  "top_k": 3
}
```

**Response**

```json
{
  "verdict": "Hallucinated",
  "confidence": 92.0,
  "confidence_score": 92.0,
  "reason": "The response incorrectly attributes the invention of the telephone to Thomas Edison. Retrieved context confirms Alexander Graham Bell invented the telephone in 1876.",
  "explanation": "The response incorrectly attributes the invention of the telephone to Thomas Edison. Retrieved context confirms Alexander Graham Bell invented the telephone in 1876.",
  "retrieved_evidence": [
    {
      "document_name": "telephone.txt",
      "content": "Alexander Graham Bell was a Scottish-born inventor...",
      "similarity_score": 0.91
    }
  ],
  "similarity_scores": [0.91],
  "metadata": {
    "top_k_requested": 3,
    "evidence_count": 1,
    "model_used": "Llama-3.2-3B-RAG-Judge"
  }
}
```

### `POST /api/upload`

Uploads a `.txt` or `.pdf` document, extracts its text (with OCR fallback for scanned PDFs), chunks it, computes an MD5 hash, generates embeddings, and indexes it into the `document_chunks` vector table.

**Request:** `multipart/form-data` with a `file` field.

**Response**

```json
{
  "status": "success",
  "filename": "einstein.txt",
  "chunks_ingested": 4,
  "message": "Successfully ingested 'einstein.txt' with 4 text chunk(s)!"
}
```

### `GET /api/history`

Returns the most recent hallucination-detection evaluations, ordered by most recent first.

**Query Parameters:** `limit` (default: `10`)

```json
[
  {
    "id": 12,
    "query": "Who invented the telephone?",
    "llm_response": "Thomas Edison invented the telephone.",
    "verdict": "Hallucinated",
    "confidence": 92.0,
    "reason": "...",
    "created_at": "2026-07-29T10:15:00"
  }
]
```

### `GET /api/stats`

Returns aggregate statistics for the analytics dashboard.

```json
{
  "total_evaluations": 48,
  "supported_count": 31,
  "hallucinated_count": 17,
  "hallucination_rate": 35.42
}
```

### `GET /api/health`

Simple liveness/health check.

```json
{
  "status": "healthy",
  "service": "GroundTruth AI Engine",
  "version": "3.1.0"
}
```

---

## Frontend

The frontend is intentionally dependency-free (no bundler, no framework) and is served directly by FastAPI's `StaticFiles` mount at `/static`, with clean top-level routes:

- **`/`** — Detector: submit a query + LLM response, watch the pipeline tracker animate through Context Retrieval → Claim Verification → Verdict Judgment, then view the verdict banner, confidence gauge, explanation, and evidence provenance cards.
- **`/dashboard`** — Aggregate telemetry: total evaluations, hallucination rate, and verdict distribution.
- **`/history`** — Chronological log of every evaluation ever run.

---

## Roadmap

- [ ] Multi-model judge ensemble (cross-validate Ollama verdicts against a secondary LLM)
- [ ] Per-document knowledge base management (delete/re-index individual sources)
- [ ] Streaming verdict responses via Server-Sent Events
- [ ] Authentication & multi-tenant knowledge bases
- [ ] Automated evaluation benchmark suite for judge accuracy

---

## License

This project is available under the MIT License. See `LICENSE` for details.