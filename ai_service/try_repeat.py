import time

from .api import generate_questions

DOC_ID = 5      # your report's id in the backend (the id Swagger showed)
RUNS = 8
COUNT = 5

full = 0
for i in range(RUNS):
    t = time.time()
    res = generate_questions(DOC_ID, "mcq", "medium", COUNT)
    got = len(res["questions"])
    full += got == COUNT
    print(
        f"run {i + 1}: got {got}/{COUNT} in {time.time() - t:.0f}s "
        f"error={res.get('error')} rejected={res.get('rejected')}"
    )
print(f"\nfull count: {full}/{RUNS}")