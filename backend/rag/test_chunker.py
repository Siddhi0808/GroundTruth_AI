from backend.rag.chunker import chunker

with open("data/documents/telephone.txt", "r", encoding="utf-8") as f:
    text = f.read()

chunks = chunker.split(text)

print(f"Total chunks: {len(chunks)}")

for i, chunk in enumerate(chunks, start=1):
    print("-" * 40)
    print(f"Chunk {i}")
    print(chunk)
