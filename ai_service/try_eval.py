"""Runs a test set through answer_question (real LLM calls).

IN_SCOPE items are (question, acceptable PDF pages). Use None to skip the page
check. A question passes when it is found AND at least one cited source page
falls inside the acceptable pages.
"""
import time

from .api import answer_question

DOC_ID = 999

# Fill the page sets by searching your PDF (Ctrl+F). Use the PDF viewer's page
# number, not the number printed on the page.
IN_SCOPE = [
    ("What is ShieldNet?", None),
    ("How does ShieldNet keep reporters anonymous?", None),
    ("Which tools and technologies were used to build the project?", None),
    ("How was the system tested?", None),
    ("What future work is proposed?", None),
    ("Where was the application deployed?", None),
    # vague / paraphrased, add yours:
    ("Summarize the conclusion of the project.", None),
    ("What does the testing chapter cover?", None),
]

# Related-sounding but NOT answered in the document.
# Check each one with Ctrl+F in the PDF before you trust it.
OUT_OF_SCOPE = [
    "How do I bake a chocolate cake?",
    "Explain the theory of relativity.",
    "Who won the 2018 football world cup?",
    "What is the capital of France?",
    "How do I change a car tyre?",
    "What is the recipe for biryani?",
    # tricky ones:
    "What is the pricing of Render's paid plans?",
    "What does the Cyber Crime law of Pakistan say about harassment penalties?",
    "How many users does ShieldNet have today?",
    "Which programming language is best for beginners?",
]


def pages_of(res: dict) -> set[int]:
    pages: set[int] = set()
    for s in res["sources"]:
        pages.update(range(s["page"], s["page_end"] + 1))
    return pages


def main() -> None:
    print("\nIN SCOPE (should be found, with the right pages)")
    ok_in = 0
    for q, expected in IN_SCOPE:
        res = answer_question(DOC_ID, q)
        good = res["found"]
        if good and expected is not None:
            good = bool(pages_of(res) & set(expected))
        ok_in += good
        cited = ",".join(str(s["page"]) for s in res["sources"]) or "-"
        err = f" error={res['error']}" if res.get("error") else ""
        print(f"  {'OK  ' if good else 'FAIL'} found={res['found']!s:5} pages={cited:9} {q}{err}")
        time.sleep(1)  # be gentle with free-tier limits
    print(f"  -> {ok_in}/{len(IN_SCOPE)} correct")

    print("\nOUT OF SCOPE (should NOT be found)")
    ok_out = 0
    for q in OUT_OF_SCOPE:
        res = answer_question(DOC_ID, q)
        good = not res["found"]
        ok_out += good
        cited = ",".join(str(s["page"]) for s in res["sources"]) or "-"
        err = f" error={res['error']}" if res.get("error") else ""
        print(f"  {'OK  ' if good else 'FAIL'} found={res['found']!s:5} pages={cited:9} {q}{err}")
        time.sleep(1)
    print(f"  -> {ok_out}/{len(OUT_OF_SCOPE)} correct")


main()