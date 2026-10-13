import threading

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_service import api as ai
from documents.models import Document

from django.utils import timezone

from .models import QuizAttempt
from .serializers import (
    ChatRequestSerializer,
    GenerateRequestSerializer,
    SubmitRequestSerializer,
)

# at most 2 question generations at the same time (avoids the rate limit)
generation_slots = threading.BoundedSemaphore(2)


def generate_limited(*args, **kwargs):
    if not generation_slots.acquire(timeout=120):
        raise RuntimeError("Server is busy, try again.")
    try:
        return ai.generate_questions(*args, **kwargs)
    finally:
        generation_slots.release()


def get_ready_document(document_id, user):
    """Returns (document, error_response). Only the owner's documents."""
    try:
        doc = Document.objects.get(id=document_id, user=user)
    except Document.DoesNotExist:
        return None, Response({"detail": "Document not found."}, status=404)
    if doc.status != "ready":
        return None, Response(
            {"detail": f"Document is not ready (status: {doc.status})."}, status=409
        )
    return doc, None


def public_question(index, q):
    """Question as the student sees it: no answer, no explanation."""
    hidden = ("correct_index", "explanation")
    data = {k: v for k, v in q.items() if k not in hidden}
    data["index"] = index
    return data


def get_attempt(attempt_id, user):
    try:
        return QuizAttempt.objects.get(id=attempt_id, user=user), None
    except QuizAttempt.DoesNotExist:
        return None, Response({"detail": "Attempt not found."}, status=404)


class ChatView(APIView):
    @extend_schema(request=ChatRequestSerializer)
    def post(self, request):
        s = ChatRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        doc, err = get_ready_document(s.validated_data["document_id"], request.user)
        if err:
            return err

        try:
            result = ai.answer_question(doc.id, s.validated_data["question"])
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception:
            return Response(
                {"answer": "", "found": False, "sources": [], "error": "ai_failed"},
                status=502,
            )
        return Response(result)


class GenerateView(APIView):
    @extend_schema(request=GenerateRequestSerializer)
    def post(self, request):
        s = GenerateRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        doc, err = get_ready_document(data["document_id"], request.user)
        if err:
            return err

        try:
            result = generate_limited(
                doc.id,
                data["question_type"],
                data["difficulty"],
                data["count"],
                chapter=data.get("chapter") or None,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception:
            return Response(
                {"questions": [], "requested": data["count"], "warnings": [], "error": "ai_failed"},
                status=502,
            )
        return Response(result)


class StartQuizView(APIView):
    @extend_schema(request=GenerateRequestSerializer)
    def post(self, request):
        s = GenerateRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        doc, err = get_ready_document(data["document_id"], request.user)
        if err:
            return err

        try:
            result = generate_limited(
                doc.id,
                data["question_type"],
                data["difficulty"],
                data["count"],
                chapter=data.get("chapter") or None,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception:
            return Response({"detail": "AI service failed.", "error": "ai_failed"}, status=502)

        questions = result.get("questions", [])
        if not questions:
            return Response(
                {
                    "detail": "No questions could be generated.",
                    "error": result.get("error"),
                    "warnings": result.get("warnings", []),
                },
                status=422,
            )

        attempt = QuizAttempt.objects.create(
            document=doc,
            user=request.user,
            question_type=data["question_type"],
            difficulty=data["difficulty"],
            questions=questions,
            total=sum(1 for q in questions if q.get("type") == "mcq"),
        )
        return Response(
            {
                "attempt_id": attempt.id,
                "questions": [public_question(i, q) for i, q in enumerate(questions)],
                "requested": data["count"],
                "warnings": result.get("warnings", []),
            },
            status=201,
        )


class SubmitQuizView(APIView):
    @extend_schema(request=SubmitRequestSerializer)
    def post(self, request, attempt_id):
        attempt, err = get_attempt(attempt_id, request.user)
        if err:
            return err
        if attempt.submitted_at:
            return Response({"detail": "This attempt was already submitted."}, status=409)

        s = SubmitRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        answers = s.validated_data["answers"]

        score = 0
        total = 0
        for i, q in enumerate(attempt.questions):
            if q.get("type") == "mcq":
                total += 1
                if answers.get(str(i)) == q.get("correct_index"):
                    score += 1

        attempt.answers = answers
        attempt.score = score
        attempt.total = total
        attempt.submitted_at = timezone.now()
        attempt.save()

        return Response({"attempt_id": attempt.id, "score": score, "total": total})


class ReviewQuizView(APIView):
    def get(self, request, attempt_id):
        attempt, err = get_attempt(attempt_id, request.user)
        if err:
            return err
        if not attempt.submitted_at:
            return Response({"detail": "Submit the attempt first."}, status=409)

        items = []
        for i, q in enumerate(attempt.questions):
            item = dict(q)
            item["index"] = i
            if q.get("type") == "mcq":
                selected = attempt.answers.get(str(i))
                item["selected_index"] = selected
                item["is_correct"] = selected == q.get("correct_index")
            items.append(item)

        return Response(
            {
                "attempt_id": attempt.id,
                "score": attempt.score,
                "total": attempt.total,
                "questions": items,
            }
        )


class AttemptHistoryView(APIView):
    def get(self, request):
        attempts = QuizAttempt.objects.filter(user=request.user).order_by("-created_at")
        document_id = request.query_params.get("document_id")
        if document_id:
            attempts = attempts.filter(document_id=document_id)

        return Response(
            [
                {
                    "attempt_id": a.id,
                    "document_id": a.document_id,
                    "question_type": a.question_type,
                    "difficulty": a.difficulty,
                    "score": a.score,
                    "total": a.total,
                    "created_at": a.created_at,
                    "submitted_at": a.submitted_at,
                }
                for a in attempts
            ]
        )