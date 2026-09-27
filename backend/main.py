import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import requests
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend import config
from backend import database
from backend.database import DatabaseUnavailable, DetectionHistory, get_db, init_db
from backend.llm.judge import INSUFFICIENT, evaluate_hallucination
from backend.rag.document_loader import SUPPORTED_EXTENSIONS, DocumentParseError, extract_text, file_hash
from backend.rag.embeddings import EmbeddingUnavailable
from backend.rag.ingest import index_document, prepare_chunks
from backend.rag.retriever import RetrievalUnavailable, retrieve_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("groundtruth_ai")

VERSION = "3.2.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Fails startup (fail fast) if the database is unreachable and SQLite fallback is disabled.
    init_db()
    logger.info("Database initialised: %s", database.database_status())
    yield


app = FastAPI(
    title="GroundTruth AI",
    description="RAG-Based LLM Hallucination Detection Engine",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = config.BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ---------------------------------------------------------------------------------------------
# Errors: safe messages for clients, full details in server logs
# ---------------------------------------------------------------------------------------------
def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": code, "message": message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = uuid.uuid4().hex[:12]
    logger.exception("Unhandled error %s on %s %s", error_id, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": {"error": "internal_error", "message": "An internal error occurred.", "error_id": error_id}},
    )


# ---------------------------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------------------------
NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2)]


class DetectionRequest(BaseModel):
    query: NonBlankText = Field(..., json_schema_extra={"example": "Who invented the telephone?"})
    llm_response: NonBlankText = Field(..., json_schema_extra={"example": "Thomas Edison invented the telephone."})
    top_k: Optional[int] = Field(default=3, ge=1, le=10)


class EvidenceItem(BaseModel):
    document_name: str
    content: str
    similarity_score: float


class DetectionResponse(BaseModel):
    verdict: str
    confidence: float
    confidence_score: float
    reason: str
    explanation: str
    retrieved_evidence: List[EvidenceItem]
    similarity_scores: List[float]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------------------------
# Frontend routes
# ---------------------------------------------------------------------------------------------
def _page(name: str) -> FileResponse:
    path = FRONTEND_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(str(path))


@app.get("/", response_class=FileResponse)
async def serve_index():
    return _page("index.html")


@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    return _page("dashboard.html")


@app.get("/history", response_class=FileResponse)
async def serve_history():
    return _page("history.html")


# ---------------------------------------------------------------------------------------------
# API. Handlers are plain `def` on purpose: they call blocking libraries (psycopg2, SQLAlchemy,
# SentenceTransformers, requests, pypdf), so FastAPI runs them in its threadpool instead of on the event loop.
# ---------------------------------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    db_info = database.database_status()
    try:
        with database.engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        db_info["reachable"] = True
    except Exception:
        logger.warning("Health check: database unreachable", exc_info=True)
        db_info["reachable"] = False
    llm = {"enabled": config.USE_LLM, "model": config.OLLAMA_MODEL, "reachable": None}
    if config.USE_LLM:
        try:
            llm["reachable"] = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=1.5).status_code == 200
        except requests.RequestException:
            llm["reachable"] = False
    degraded = db_info["fallback_active"] or not db_info["reachable"] or (config.USE_LLM and not llm["reachable"])
    return {"status": "degraded" if degraded else "healthy", "service": "GroundTruth AI Engine",
            "version": VERSION, "database": db_info, "llm": llm}


@app.post("/detect", response_model=DetectionResponse)
@app.post("/api/detect", response_model=DetectionResponse)
def detect_hallucination(request: DetectionRequest, db: Session = Depends(get_db)):
    top_k = request.top_k or 3
    try:
        retrieved_docs = retrieve_context(request.query, top_k=top_k)
    except RetrievalUnavailable:
        logger.exception("Retrieval unavailable for /detect")
        raise api_error(503, "retrieval_unavailable",
                        "Evidence retrieval is temporarily unavailable, so no verdict was produced.")

    evidence_list, similarity_scores, context_texts = [], [], []
    for doc in retrieved_docs:
        score = round(float(doc.get("score", 0.0)), 4)
        source = doc.get("source") or "Knowledge Base"
        text = doc.get("content") or ""
        evidence_list.append(EvidenceItem(document_name=source, content=text, similarity_score=score))
        similarity_scores.append(score)
        context_texts.append(f"[{source}]: {text}")

    if not retrieved_docs:
        result = {"verdict": INSUFFICIENT, "confidence": 0.0, "engine": "none", "model": None, "fallback_reason": None,
                  "reason": "No evidence was retrieved from the knowledge base, so the response cannot be verified."}
    else:
        result = evaluate_hallucination(request.query, request.llm_response, "\n\n".join(context_texts))

    confidence_pct = round(float(result["confidence"]) * 100, 2)
    reason = result["reason"]

    history_saved = True
    try:
        db.add(DetectionHistory(query=request.query, llm_response=request.llm_response, verdict=result["verdict"],
                                confidence=confidence_pct, reason=reason, engine=result["engine"]))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        history_saved = False
        logger.exception("Failed to record detection history")

    db_info = database.database_status()
    return DetectionResponse(
        verdict=result["verdict"],
        confidence=confidence_pct,
        confidence_score=confidence_pct,
        reason=reason,
        explanation=reason,
        retrieved_evidence=evidence_list,
        similarity_scores=similarity_scores,
        metadata={
            "top_k_requested": top_k,
            "evidence_count": len(evidence_list),
            "engine": result["engine"],
            "model_used": result["model"],
            "fallback_reason": result["fallback_reason"],
            "database_backend": db_info["backend"],
            "retrieval_mode": db_info["retrieval_mode"],
            "degraded": bool(db_info["fallback_active"] or result["fallback_reason"] not in (None, "llm_disabled")),
            "history_saved": history_saved,
        },
    )


_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def safe_display_name(filename: Optional[str]) -> str:
    """Never trust the client filename: keep only the last path component and an allow-listed character set."""
    name = (filename or "").replace("\\", "/").split("/")[-1]
    name = _SAFE_CHARS.sub("_", name).strip("._")[:80]
    return name or "document"


def resolve_inside(directory: Path, name: str) -> Path:
    base = directory.resolve()
    target = (base / name).resolve()
    if target.parent != base:
        raise api_error(400, "invalid_filename", "Invalid file name.")
    return target


@app.post("/api/upload")
def upload_document(file: UploadFile = File(...)):
    """Validate, extract, deduplicate (by SHA-256 of the file bytes), chunk, embed and index a .txt/.pdf file.

    Consistency: the file is written to a temporary name, chunks are inserted, the file is atomically renamed
    into place, then the transaction commits. Any failure removes the temporary/new file and rolls back.
    """
    display_name = safe_display_name(file.filename)
    extension = Path(display_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise api_error(400, "unsupported_file_type", "Unsupported file format. Please upload a .txt or .pdf file.")

    data = file.file.read()
    if not data:
        raise api_error(400, "empty_file", "The uploaded file is empty.")
    try:
        text = extract_text(data, extension)
    except DocumentParseError as exc:
        raise api_error(400, "invalid_document", str(exc))
    if not text.strip():
        raise api_error(400, "no_text", "No text could be extracted from the file (scanned PDF without OCR, or empty).")

    digest = file_hash(data)
    storage_name = f"{digest[:16]}_{display_name}"
    config.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = resolve_inside(config.DOCUMENTS_DIR, storage_name)
    duplicate = lambda existing: {  # noqa: E731
        "status": "duplicate", "filename": existing, "chunks_ingested": 0,
        "message": f"This document is already indexed as '{existing}'; nothing was added.",
    }

    try:
        with database.db_connection() as conn:
            existing = database.find_document_by_hash(conn, digest)
            if existing:
                return duplicate(existing)

            chunks, embeddings = prepare_chunks(text)
            if not chunks:
                raise api_error(400, "no_text", "No indexable text was found in the file.")

            tmp = dest.with_name(f".{uuid.uuid4().hex}.uploading")
            existed_before = dest.exists()
            moved = False
            try:
                tmp.write_bytes(data)
                inserted = index_document(conn, storage_name, digest, chunks, embeddings)
                if inserted == 0:  # a concurrent upload of identical content committed first
                    conn.rollback()
                    return duplicate(database.find_document_by_hash(conn, digest) or storage_name)
                os.replace(tmp, dest)
                moved = True
                conn.commit()
            except BaseException:
                if moved and not existed_before:
                    dest.unlink(missing_ok=True)
                raise
            finally:
                tmp.unlink(missing_ok=True)  # no-op after a successful os.replace
    except HTTPException:
        raise
    except (DatabaseUnavailable, EmbeddingUnavailable):
        logger.exception("Upload failed: dependency unavailable")
        raise api_error(503, "service_unavailable", "The document index is temporarily unavailable. Please retry.")
    except Exception:
        # Driver errors surface here (the connection was rolled back and closed by db_connection()).
        error_id = uuid.uuid4().hex[:12]
        logger.exception("Upload failed (error_id=%s)", error_id)
        raise HTTPException(status_code=500, detail={"error": "upload_failed",
                                                     "message": "The document could not be indexed.",
                                                     "error_id": error_id})

    return {
        "status": "success",
        "filename": storage_name,
        "original_filename": display_name,
        "chunks_ingested": inserted,
        "message": f"Successfully ingested '{display_name}' with {inserted} text chunk(s).",
    }


@app.get("/api/history")
def get_history(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    try:
        records = db.query(DetectionHistory).order_by(DetectionHistory.created_at.desc()).limit(limit).all()
    except SQLAlchemyError:
        logger.exception("Failed to read history")
        raise api_error(503, "database_unavailable", "History is temporarily unavailable.")
    return [
        {
            "id": r.id,
            "query": r.query,
            "llm_response": r.llm_response,
            "verdict": r.verdict,
            "confidence": round(r.confidence, 2) if r.confidence is not None else None,
            "reason": r.reason,
            "engine": r.engine,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    try:
        rows = db.query(DetectionHistory.verdict, func.count(DetectionHistory.id)).group_by(DetectionHistory.verdict).all()
    except SQLAlchemyError:
        logger.exception("Failed to compute stats")
        raise api_error(503, "database_unavailable", "Statistics are temporarily unavailable.")
    counts = {verdict: n for verdict, n in rows}
    total = sum(counts.values())
    hallucinated = counts.get("Hallucinated", 0)
    return {
        "total_evaluations": total,
        "supported_count": counts.get("Supported", 0),
        "hallucinated_count": hallucinated,
        "insufficient_evidence_count": counts.get(INSUFFICIENT, 0),
        "hallucination_rate": round(hallucinated / total * 100, 2) if total else 0.0,
    }
