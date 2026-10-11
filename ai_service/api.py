"""
AI service contract. The backend calls ONLY these functions.
Heavy libraries are imported inside the functions, so `import ai_service`
works even where the AI libraries are not installed yet.
"""


def process_document(document_id: int, file_path: str) -> dict:
    """Extract text, chunk, embed and store the document.

    Returns: {"status": "ready" | "failed", "pages": int, "chunks": int,
              "warnings": [str]}
    """
    from .chunk import chunk_pages
    from .extract import extract_document
    from .store import store_chunks

    def failed(msg: str, pages: int = 0, warnings: list[str] | None = None) -> dict:
        return {
            "status": "failed",
            "pages": pages,
            "chunks": 0,
            "warnings": (warnings or []) + [msg],
        }

    try:
        doc = extract_document(file_path)
        chunks = chunk_pages(doc.pages)
    except (FileNotFoundError, ValueError) as exc:
        return failed(str(exc))
    except Exception:
        return failed("This file could not be read. It may be corrupted or protected.")

    if not chunks:
        return failed(
            "No searchable text was found in this file.",
            pages=len(doc.pages),
            warnings=list(doc.warnings),
        )
    try:
        store_chunks(document_id, chunks)
    except Exception:
        return failed("The document could not be stored for search.", pages=len(doc.pages))

    return {
        "status": "ready",
        "pages": len(doc.pages),
        "chunks": len(chunks),
        "warnings": list(doc.warnings),
    }


def answer_question(document_id: int, question: str) -> dict:
    """Answer only from the document. If nothing relevant, found=False.

    Returns: {
        "answer": str,
        "found": bool,
        "sources": [{"chapter": str | None, "page": int, "page_end": int,
                     "snippet": str}],
        "error": "llm_unavailable" | "bad_llm_output"   # only when something broke
    }
    """
    from .answer import answer

    return answer(document_id, question)


def generate_questions(
    document_id: int,
    question_type: str,  # "mcq" | "short" | "long" | "mixed"
    difficulty: str,  # "low" | "medium" | "high"
    count: int,  # 1..20
    chapter: str | None = None,  # one of the strings from list_chapters()
) -> dict:
    """Generate validated questions from the document.

    Returns: {
        "questions": [item, ...],       # can be FEWER than requested
        "requested": int,
        "warnings": [str],              # show these to the user
        "error": "llm_unavailable" | "chapter_not_found" | "no_content"  # only if nothing came back
    }
    MCQ item: {"type": "mcq", "question": str, "options": [4 strings],
               "correct_index": int, "explanation": str, "difficulty": str,
               "source": {"chapter": str | None, "page": int, "page_end": int, "snippet": str}}
    Written item: {"type": "short" | "long", "question": str,
                   "model_answer": str, "difficulty": str, "source": {...}}
    Raises ValueError for an invalid type, difficulty or count (validate before calling).
    """
    from .generate import generate

    return generate(document_id, question_type, difficulty, count, chapter)


def list_chapters(document_id: int) -> list[str]:
    """Chapter names found in the document, in order (for the chapter dropdown)."""
    from .generate import list_chapters as _list

    return _list(document_id)


def delete_document(document_id: int) -> None:
    """Remove everything stored for this document (call when a document is deleted)."""
    from .store import delete_document as _delete

    _delete(document_id)