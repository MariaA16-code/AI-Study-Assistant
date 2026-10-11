import sys

from .api import generate_questions, list_chapters

DOC_ID = 999  # the document stored earlier by try_store
kind = sys.argv[1] if len(sys.argv) > 1 else "mcq"
difficulty = sys.argv[2] if len(sys.argv) > 2 else "medium"
count = int(sys.argv[3]) if len(sys.argv) > 3 else 3
chapter = " ".join(sys.argv[4:]) or None

print("chapters:", list_chapters(DOC_ID))
res = generate_questions(DOC_ID, kind, difficulty, count, chapter)
print(
    f"got {len(res['questions'])} of {res['requested']} | error={res.get('error')} "
    f"| warnings={res['warnings']} | rejected={res.get('rejected')}"
)
for i, q in enumerate(res["questions"], start=1):
    s = q["source"]
    print(f"\n{i}. [{q['type']}/{q['difficulty']}] {q['question']}")
    if q["type"] == "mcq":
        for j, opt in enumerate(q["options"]):
            mark = "*" if j == q["correct_index"] else " "
            print(f"   {mark} {'ABCD'[j]}. {opt}")
        print("   why:", q["explanation"])
    else:
        print("   answer:", q["model_answer"][:300])
    print(f"   source: {s['chapter']} | page {s['page']}")