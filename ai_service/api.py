"""
AI service contract. The backend calls ONLY these three functions.
"""


def process_document(document_id: int, file_path: str) -> dict:
    """Extract text, chunk, embed and store the document.

    Returns: {"status": "ready", "pages": int, "chunks": int, "warnings": [str]}
    """
    return {"status": "ready", "pages": 0, "chunks": 0, "warnings": ["stub"]}


def answer_question(document_id: int, question: str) -> dict:
    """Answer only from the document. If nothing relevant, found=False.

    Returns: {
        "answer": str,
        "found": bool,
        "sources": [{"chapter": str | None, "page": int | None, "snippet": str}],
    }
    """
    return {"answer": "Stub answer.", "found": False, "sources": []}


def generate_questions(
    document_id: int,
    question_type: str,  # "mcq" | "short" | "long" | "mixed"
    difficulty: str,  # "low" | "medium" | "high"
    count: int,
    chapter: str | None = None,
) -> list[dict]:
    """Generate validated questions from the document.

    MCQ item: {"type": "mcq", "question": str, "options": [4 strings],
               "correct_index": int, "explanation": str, "source": {...}}
    Written item: {"type": "short" | "long", "question": str,
                   "model_answer": str, "source": {...}}
    """
    return []