from .store import query_vectors

DOC_ID = 999  # the document stored earlier by try_store

# Edit these so they fit YOUR sample document.
IN_SCOPE = [
    "What is ShieldNet?",
    "How does ShieldNet keep reporters anonymous?",
    "Which tools and technologies were used to build the project?",
    "How was the system tested?",
    "What future work is proposed?",
    "Where was the application deployed?",
]
OUT_OF_SCOPE = [
    "How do I bake a chocolate cake?",
    "Who won the 2018 football world cup?",
    "What is the capital of France?",
    "Explain the theory of relativity.",
    "How do I change a car tyre?",
    "What is the recipe for biryani?",
]


def top_score(question: str) -> float:
    hits = query_vectors(DOC_ID, question, n_results=1)
    return hits[0]["score"] if hits else 0.0


def show(title: str, questions: list[str]) -> list[float]:
    print(f"\n{title}")
    scores = []
    for q in questions:
        s = top_score(q)
        scores.append(s)
        print(f"  {s:.3f}  {q}")
    return scores


in_scores = show("IN SCOPE (should be high)", IN_SCOPE)
out_scores = show("OUT OF SCOPE (should be low)", OUT_OF_SCOPE)

low_in, high_out = min(in_scores), max(out_scores)
gap = low_in - high_out
worst_in = min(zip(in_scores, IN_SCOPE))
worst_out = max(zip(out_scores, OUT_OF_SCOPE))

print(f"\nweakest in-scope:       {worst_in[0]:.3f}  {worst_in[1]}")
print(f"strongest out-of-scope: {worst_out[0]:.3f}  {worst_out[1]}")
print(f"gap: {gap:.3f}")
if gap >= 0.05:
    print(f"usable gap. Suggested MIN_SCORE = {round((low_in + high_out) / 2, 2)}")
else:
    print("TOO CLOSE: score alone cannot separate these. Use keyword search and the LLM check.")