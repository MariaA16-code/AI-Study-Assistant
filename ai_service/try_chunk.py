import sys

from .chunk import chunk_pages
from .extract import extract_document

doc = extract_document(sys.argv[1])
chunks = chunk_pages(doc.pages)
sizes = [len(c.text) for c in chunks]

print(len(doc.pages), "pages ->", len(chunks), "chunks")
print("avg size:", sum(sizes) // max(len(sizes), 1), "| max:", max(sizes, default=0))
for c in chunks[10:13]:
    print(f"--- chunk {c.index} | pages {c.page_start}-{c.page_end} | {c.chapter}")
    print(c.text[:200])
from collections import Counter

print("chunks per chapter:")
for chapter, n in Counter(c.chapter for c in chunks).items():
    print(f"  {n:3d}  {chapter}")   