from backend.rag.embeddings import embedding_model
from backend.database import get_connection
from sqlalchemy import text


document = """
Alexander Graham Bell was a Scottish-born inventor.
He invented the first practical telephone.
Bell received a patent for the telephone in 1876.
"""

source = "telephone.txt"


embedding = embedding_model.generate_embedding(document)


connection = get_connection()


query = text("""
INSERT INTO document_chunks
(content, source, embedding)

VALUES
(:content, :source, :embedding)
""")


connection.execute(
    query,
    {
        "content": document,
        "source": source,
        "embedding": embedding
    }
)


connection.commit()

connection.close()


print("Document stored successfully!")