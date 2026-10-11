import sys

from .extract import extract_document

doc = extract_document(sys.argv[1])
print(len(doc.pages), "pages/sections")
print("warnings:", doc.warnings)

for p in doc.pages[:3]:
    print(f"--- page {p.number} | chapter: {p.chapter} | {len(p.text)} chars")
    print(p.text[:200].replace("\n", " "))

chapters = []
for p in doc.pages:
    if p.chapter and p.chapter not in chapters:
        chapters.append(p.chapter)
print("chapters found:", chapters[:10])