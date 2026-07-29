import os
from pathlib import Path

from pypdf import PdfReader


def load_documents(folder):

    documents=[]

    path=Path(folder)


    for file in path.iterdir():

        if file.suffix.lower()==".txt":

            text=file.read_text(
                encoding="utf-8"
            )

            documents.append({

                "source":file.name,

                "content":text

            })


        elif file.suffix.lower()==".pdf":

            reader=PdfReader(file)

            text=""

            for page in reader.pages:

                text += page.extract_text() or ""


            documents.append({

                "source":file.name,

                "content":text

            })


    return documents