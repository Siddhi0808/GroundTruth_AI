import os
import getpass
import logging
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

logger = logging.getLogger("groundtruth_ai")

# Detect current system user for macOS Homebrew Postgres defaults
DEFAULT_USER = getpass.getuser()

DB_USER = os.getenv("POSTGRES_USER", DEFAULT_USER)
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "groundtruth")

# Connection string
if DB_PASSWORD:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy Setup with Fallback
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    with engine.connect() as conn:
        pass
    USE_SQLITE = False
except Exception as e:
    logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database.")
    DATABASE_URL = "sqlite:///./groundtruth_fallback.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    USE_SQLITE = True

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    llm_response = Column(Text, nullable=False)
    verdict = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_connection():
    """Provides direct raw database connections for retriever/vector queries."""
    if USE_SQLITE:
        conn = sqlite3.connect("./groundtruth_fallback.db")
        conn.row_factory = sqlite3.Row
        return conn
    else:
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            cursor_factory=RealDictCursor
        )