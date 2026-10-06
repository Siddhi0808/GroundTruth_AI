"""Central configuration: the single environment-variable contract for the app, Docker and tests.

Values come from the process environment; a `.env` file in the project root is loaded if present
(real environment variables take precedence over `.env`).
"""
import getpass
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)


def _bool(name: str, default: bool) -> bool:
    """Boolean env var; accepts 1/true/yes/on (case-insensitive)."""
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def build_database_url() -> str:
    """DATABASE_URL wins; otherwise the URL is assembled from the POSTGRES_* variables."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user = os.getenv("POSTGRES_USER", getpass.getuser())
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    name = os.getenv("POSTGRES_DB", "groundtruth")
    auth = f"{user}:{password}" if password else user
    return f"postgresql://{auth}@{host}:{port}/{name}"


# --- Database -----------------------------------------------------------------------------
# If Postgres is unreachable at startup and this is true, the app runs on SQLite in a
# clearly-reported degraded mode (keyword retrieval). Set to false in Docker/production to fail fast.
ALLOW_SQLITE_FALLBACK = _bool("ALLOW_SQLITE_FALLBACK", True)
SQLITE_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "groundtruth_fallback.db"))

# --- Documents ----------------------------------------------------------------------------
DOCUMENTS_DIR = Path(os.getenv("DOCUMENTS_DIR", str(BASE_DIR / "data" / "documents")))

# --- Embeddings & chunking ----------------------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384
# all-MiniLM-L6-v2 truncates input at 256 word-piece tokens (including [CLS]/[SEP]).
# 200-token chunks leave headroom; 40 tokens (20%) of overlap keeps boundary facts whole.
CHUNK_SIZE_TOKENS = _int("CHUNK_SIZE_TOKENS", 200)
CHUNK_OVERLAP_TOKENS = _int("CHUNK_OVERLAP_TOKENS", 40)

# --- LLM judge (Ollama) -------------------------------------------------------------------
USE_LLM = _bool("USE_LLM", True)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT_SECONDS = _float("OLLAMA_TIMEOUT_SECONDS", 35.0)
# Deterministic decoding for a judge: temperature 0 + fixed seed. This makes repeated runs far more
# repeatable on the same model/runtime, but does not guarantee identical output across versions/hardware.
LLM_TEMPERATURE = _float("LLM_TEMPERATURE", 0.0)
LLM_SEED = _int("LLM_SEED", 42)
LLM_NUM_CTX = _int("LLM_NUM_CTX", 4096)

HEURISTIC_ENGINE_NAME = "heuristic-rules-v2"
