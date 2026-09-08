import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.chunker import chunker

def test_chunker_basic():
    doc_path = PROJECT_ROOT / "data" / "documents" / "telephone.txt"
    with open(doc_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunker.split(text)
    print(f"Total chunks from {doc_path.name}: {len(chunks)}")
    for i, chunk in enumerate(chunks, start=1):
        print("-" * 40)
        print(f"Chunk {i}")
        print(chunk[:150] + "...")
    assert len(chunks) >= 1

if __name__ == "__main__":
    test_chunker_basic()
