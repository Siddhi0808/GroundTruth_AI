import os
import io
import hashlib
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pypdf

from backend.database import get_db, init_db, DetectionHistory
from backend.rag.retriever import retrieve_context
from backend.llm.judge import evaluate_hallucination

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("groundtruth_ai")

app = FastAPI(
    title="GroundTruth AI",
    description="RAG-Based LLM Hallucination Detection Engine",
    version="3.1.0"
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Pydantic Schemas
class DetectionRequest(BaseModel):
    query: str = Field(..., min_length=2, example="Who invented the telephone?")
    llm_response: str = Field(..., min_length=2, example="Thomas Edison invented the telephone.")
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

@app.on_event("startup")
def startup_event():
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization deferred: {e}")

# Frontend Routes
@app.get("/", response_class=FileResponse)
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index.html not found")

@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    dash_path = os.path.join(FRONTEND_DIR, "dashboard.html")
    if os.path.exists(dash_path):
        return FileResponse(dash_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/history", response_class=FileResponse)
async def serve_history():
    hist_path = os.path.join(FRONTEND_DIR, "history.html")
    if os.path.exists(hist_path):
        return FileResponse(hist_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Core API Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "GroundTruth AI Engine", "version": "3.1.0"}

@app.post("/detect", response_model=DetectionResponse)
@app.post("/api/detect", response_model=DetectionResponse)
async def detect_hallucination(request: DetectionRequest, db: Session = Depends(get_db)):
    try:
        # Step 1: Retrieve Evidence via RAG
        retrieved_docs = retrieve_context(request.query, top_k=request.top_k)
        
        evidence_list = []
        similarity_scores = []
        context_texts = []

        for doc in retrieved_docs:
            score = round(float(doc.get("score", 0.0)), 4)
            text = doc.get("content", doc.get("text", ""))
            source = doc.get("source", doc.get("document_name", "Knowledge Base"))
            
            evidence_list.append(EvidenceItem(
                document_name=source,
                content=text,
                similarity_score=score
            ))
            similarity_scores.append(score)
            context_texts.append(f"[{source}]: {text}")

        full_context = "\n\n".join(context_texts) if context_texts else "No relevant context found in knowledge base."

        # Step 2: LLM Evaluation
        eval_result = evaluate_hallucination(
            query=request.query,
            response=request.llm_response,
            context=full_context
        )

        verdict = eval_result.get("verdict", "Hallucinated")
        confidence = float(eval_result.get("confidence", 0.85))
        reason = eval_result.get("reason", eval_result.get("explanation", "Evaluation completed."))

        # Step 3: Save to DB History
        try:
            history_entry = DetectionHistory(
                query=request.query,
                llm_response=request.llm_response,
                verdict=verdict,
                confidence=confidence,
                reason=reason
            )
            db.add(history_entry)
            db.commit()
        except Exception as db_err:
            logger.error(f"Failed to record history: {db_err}")
            db.rollback()

        return DetectionResponse(
            verdict=verdict,
            confidence=round(confidence * 100, 2) if confidence <= 1.0 else round(confidence, 2),
            confidence_score=round(confidence * 100, 2) if confidence <= 1.0 else round(confidence, 2),
            reason=reason,
            explanation=reason,
            retrieved_evidence=evidence_list,
            similarity_scores=similarity_scores,
            metadata={
                "top_k_requested": request.top_k,
                "evidence_count": len(evidence_list),
                "model_used": "Llama-3.2-3B-RAG-Judge"
            }
        )

    except Exception as e:
        logger.error(f"Detection error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hallucination detection failed: {str(e)}"
        )

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a .txt or .pdf file, chunks it, and ingests it into the vector database matching exact schema."""
    filename = file.filename
    extracted_text = ""

    # Validate file extension
    if not (filename.endswith(".txt") or filename.endswith(".pdf")):
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Please upload a .txt or .pdf file."
        )

    try:
        file_bytes = await file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()

        # Extract text from file
        if filename.endswith(".pdf"):
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"

            # OCR Fallback for scanned/image-based PDFs
            if not extracted_text.strip():
                logger.info(f"pypdf yielded no text for {filename}. Attempting OCR fallback...")
                try:
                    import pdf2image
                    import pytesseract

                    images = pdf2image.convert_from_bytes(file_bytes)
                    for img in images:
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text:
                            extracted_text += ocr_text + "\n"
                except Exception as ocr_err:
                    logger.warning(f"OCR fallback unavailable: {ocr_err}")

        else:
            extracted_text = file_bytes.decode("utf-8")

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400, 
                detail="The uploaded PDF appears to be a scanned image or empty. Try converting it to a text-selectable PDF or uploading a .txt file."
            )

        # Save copy locally to data/documents/
        save_path = os.path.join(BASE_DIR, "data", "documents", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # RAG Ingestion Pipeline
        from backend.rag.ingest import chunk_text
        from backend.rag.embeddings import get_embedding
        from backend.database import get_connection

        chunks = chunk_text(extracted_text)
        conn = get_connection()
        cursor = conn.cursor()

        is_postgres = hasattr(conn, "status") or "psycopg" in str(type(conn)).lower()
        
        # Ensure target table exists matching schema
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

        conn.commit()

        # Insert chunks & embeddings matching table structure exactly
        inserted_count = 0
        for idx, chunk in enumerate(chunks, start=1):
            embedding = get_embedding(chunk)
            if is_postgres:
                cursor.execute(
                    """
                    INSERT INTO document_chunks (source, file_hash, chunk_number, content, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    """,
                    (filename, file_hash, idx, chunk, str(embedding))
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO document_chunks (source, file_hash, chunk_number, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    (filename, file_hash, idx, chunk)
                )
            inserted_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "filename": filename,
            "chunks_ingested": inserted_count,
            "message": f"Successfully ingested '{filename}' with {inserted_count} text chunk(s)!"
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing uploaded document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/api/history")
async def get_history(limit: int = 10, db: Session = Depends(get_db)):
    try:
        records = db.query(DetectionHistory).order_by(DetectionHistory.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "query": r.query,
                "llm_response": r.llm_response,
                "verdict": r.verdict,
                "confidence": r.confidence,
                "reason": r.reason,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return []

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    try:
        total = db.query(DetectionHistory).count()
        supported = db.query(DetectionHistory).filter(DetectionHistory.verdict.ilike("Supported")).count()
        hallucinated = db.query(DetectionHistory).filter(DetectionHistory.verdict.ilike("Hallucinated")).count()
        
        return {
            "total_evaluations": total,
            "supported_count": supported,
            "hallucinated_count": hallucinated,
            "hallucination_rate": round((hallucinated / total * 100), 2) if total > 0 else 0.0
        }
    except Exception as e:
        return {"total_evaluations": 0, "supported_count": 0, "hallucinated_count": 0, "hallucination_rate": 0.0}