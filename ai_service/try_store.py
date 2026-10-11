import sys
import time

from .chunk import chunk_pages
from .extract import extract_document
from .store import query_vectors, store_chunks

path = sys.argv[1]
question = " ".join(sys.argv[2:]) or "What is the purpose of this project?"

t = time.time()
chunks = chunk_pages(extract_document(path).pages)
store_chunks(999, chunks)
print(f"stored {len(chunks)} chunks in {round(time.time() - t, 1)} s")

t = time.time()
for hit in query_vectors(999, question, n_results=3):
    print(f"--- score {hit['score']} | pages {hit['page_start']}-{hit['page_end']} | {hit['chapter']}")
    print(hit["text"][:200])
print(f"search took {round(time.time() - t, 1)} s")