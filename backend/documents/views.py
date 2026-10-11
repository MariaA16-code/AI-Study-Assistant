import threading

from django.db import close_old_connections
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from ai_service import api as ai

from .models import Document
from .serializers import DocumentSerializer


def run_processing(doc_id):
    """Runs in a background thread so the upload returns immediately."""
    close_old_connections()
    doc = Document.objects.get(id=doc_id)
    try:
        result = ai.process_document(doc.id, doc.file.path)
        doc.status = result.get("status", "failed")
        doc.warnings = result.get("warnings", [])
        doc.pages = result.get("pages")
        doc.chunks = result.get("chunks")
    except Exception as e:
        doc.status = "failed"
        doc.warnings = [f"Processing error: {e}"]
    doc.save()
    close_old_connections()


class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Document.objects.order_by("-created_at")
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        f = self.request.FILES["file"]
        doc = serializer.save(title=self.request.data.get("title") or f.name)
        threading.Thread(target=run_processing, args=(doc.id,), daemon=True).start()

    def perform_destroy(self, instance):
        try:
            ai.delete_document(instance.id)
        except Exception:
            pass  # still delete our side even if the AI cleanup fails
        instance.file.delete(save=False)
        instance.delete()

    @action(detail=True, methods=["get"])
    def chapters(self, request, pk=None):
        doc = self.get_object()
        try:
            names = ai.list_chapters(doc.id)
        except Exception:
            names = []
        return Response({"chapters": names})