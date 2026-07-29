from pathlib import Path

from backend.rag.document_loader import load_documents
from backend.rag.embeddings import get_embedding
from backend.database import get_connection

from sqlalchemy import text


DOCUMENT_FOLDER = "data/documents"



def chunk_text(text, chunk_size=500):

    words = text.split()

    chunks=[]

    for i in range(0, len(words), chunk_size):

        chunk = " ".join(
            words[i:i+chunk_size]
        )

        chunks.append(chunk)

    return chunks




def ingest():

    documents = load_documents(
        DOCUMENT_FOLDER
    )


    connection = get_connection()


    for doc in documents:


        existing = connection.execute(

            text(
            """
            SELECT COUNT(*)
            FROM document_chunks
            WHERE source=:source
            """
            ),

            {
                "source":doc["source"]
            }

        ).scalar()



        if existing:

            print(
                f"✓ Skipping {doc['source']} (unchanged)"
            )

            continue



        chunks = chunk_text(
            doc["content"]
        )


        print(
            f"{doc['source']}: {len(chunks)} chunks"
        )



        for index, chunk in enumerate(chunks):


            embedding = get_embedding(
                chunk
            )


            connection.execute(

                text(
                """
                INSERT INTO document_chunks
                (
                    content,
                    source,
                    embedding
                )

                VALUES
                (
                    :content,
                    :source,
                    :embedding
                )
                """
                ),

                {

                    "content":chunk,

                    "source":doc["source"],

                    "embedding":str(embedding)

                }

            )


        connection.commit()


        print(
            f"✓ Stored {doc['source']}"
        )



    connection.close()



if __name__=="__main__":

    ingest()