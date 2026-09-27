"""Text extraction shared by the upload endpoint and batch ingestion.

Both paths hash the RAW FILE BYTES (SHA-256), so the same file produces the same `file_hash` no matter how
it enters the system; that hash is the deduplication key in the database.
"""
import hashlib
import io
import logging
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger("groundtruth_ai")

SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


class DocumentParseError(ValueError):
    """The file is not a readable .txt/.pdf document. Message is safe to show to users."""


def file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_text(data: bytes, extension: str, allow_ocr: bool = True) -> str:
    extension = extension.lower()
    if extension == ".txt":
        if b"\x00" in data:
            raise DocumentParseError("The .txt file contains binary data.")
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentParseError("The .txt file is not valid UTF-8 text.") from exc

    if extension == ".pdf":
        if not data.lstrip().startswith(b"%PDF-"):
            raise DocumentParseError("The file does not look like a PDF.")
        try:
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        except (PdfReadError, ValueError, KeyError, TypeError) as exc:
            raise DocumentParseError("The PDF could not be parsed.") from exc
        if not text.strip() and allow_ocr:
            text = _ocr_pdf(data)
        return text

    raise DocumentParseError("Unsupported file format. Please upload a .txt or .pdf file.")


def _ocr_pdf(data: bytes) -> str:
    """OCR fallback for scanned/image-only PDFs (needs poppler + tesseract installed)."""
    logger.info("pypdf yielded no text; attempting OCR fallback")
    try:
        import pdf2image
        import pytesseract

        return "\n".join(pytesseract.image_to_string(img) for img in pdf2image.convert_from_bytes(data))
    except Exception:
        logger.warning("OCR fallback unavailable or failed", exc_info=True)
        return ""


def load_documents(folder) -> List[Dict]:
    """Read every .txt/.pdf in `folder` (non-recursive). Unreadable files are logged and skipped
    instead of aborting the whole ingest."""
    documents = []
    for path in sorted(Path(folder).iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS or not path.is_file():
            continue
        data = path.read_bytes()
        try:
            text = extract_text(data, path.suffix, allow_ocr=False)
        except DocumentParseError as exc:
            logger.warning("Skipping %s: %s", path.name, exc)
            continue
        documents.append({"source": path.name, "content": text, "file_hash": file_hash(data)})
    return documents
