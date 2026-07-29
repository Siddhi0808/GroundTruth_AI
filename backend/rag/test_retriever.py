from backend.rag.retriever import retriever

query = "Who invented the telephone?"

results = retriever.retrieve(query)

print("\nRetrieved Chunks\n")

for row in results:
    print("=" * 60)
    print(f"Source : {row.source}")
    print(f"Chunk  : {row.chunk_number}")
    print(f"Distance : {row.distance:.4f}")
    print()
    print(row.content)