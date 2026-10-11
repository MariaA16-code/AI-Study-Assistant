from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_service import api as ai
from documents.models import Document

from .serializers import ChatRequestSerializer, GenerateRequestSerializer


def get_ready_document(document_id):
    """Returns (document, error_response)."""
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return None, Response({"detail": "Document not found."}, status=404)
    if doc.status != "ready":
        return None, Response(
            {"detail": f"Document is not ready (status: {doc.status})."}, status=409
        )
    return doc, None


class ChatView(APIView):
    @extend_schema(request=ChatRequestSerializer)
    def post(self, request):
        s = ChatRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        doc, err = get_ready_document(s.validated_data["document_id"])
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

        doc, err = get_ready_document(data["document_id"])
        if err:
            return err

        try:
            result = ai.generate_questions(
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