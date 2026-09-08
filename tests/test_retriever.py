import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.retriever import retriever

def test_retriever_query():
    query = "Who invented the telephone?"
    results = retriever.retrieve(query, top_k=3)
    print("\nRetrieved Chunks:\n")
    for row in results:
        print("=" * 60)
        print(f"Source   : {row.source}")
        print(f"Chunk    : {row.chunk_number}")
        print(f"Score    : {row.score}")
        print(f"Distance : {row.distance:.4f}")
        print(row.content[:200] + "...\n")
    assert len(results) > 0

if __name__ == "__main__":
    test_retriever_query()
