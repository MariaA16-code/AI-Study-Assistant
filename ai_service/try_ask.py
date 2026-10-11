import sys

from .api import answer_question

res = answer_question(999, " ".join(sys.argv[1:]))  # 999 = document stored by try_store
print("found:", res["found"])
print("answer:", res["answer"])
for s in res["sources"]:
    print(f"  - {s['chapter']} | page {s['page']}: {s['snippet'][:80]}")
if res.get("error"):
    print("error:", res["error"])