import threading

from decouple import config
from django.db import close_old_connections
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from ai_service import api as ai

from .models import Document
from .serializers import (
    MAX_FILES,
    DocumentSerializer,
    DocumentUploadSerializer,
    validate_upload,
)

# How many documents are processed at the same time.
# Keep 1 until Maria confirms it is safe. Then set PROCESS_WORKERS=2 in .env
PROCESS_WORKERS = config("PROCESS_WORKERS", default=1, cast=int)
process_slots = threading.Semaphore(PROCESS_WORKERS)


def run_processing(doc_id):
    """Runs in a background thread so the upload returns immediately."""
    with process_slots:
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
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # each student sees only their own documents
        return Document.objects.filter(user=self.request.user).order_by("-created_at")

    @extend_schema(
        request={"multipart/form-data": DocumentUploadSerializer},
        responses={201: DocumentSerializer(many=True)},
    )
    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist("files") + request.FILES.getlist("file")
        single_old_way = (
            len(files) == 1
            and len(request.FILES.getlist("files")) == 0
        )

        if not files:
            return Response(
                {"files": ["No file was uploaded."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(files) > MAX_FILES:
            return Response(
                {"files": [f"Too many files (max {MAX_FILES} per upload)."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check every file first, so nothing is saved if one file is bad
        errors = {}
        for f in files:
            try:
                validate_upload(f)
            except ValidationError as e:
                errors[f.name] = e.detail
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        title_from_user = request.data.get("title") if len(files) == 1 else None

        created = []
        for f in files:
            serializer = DocumentSerializer(
                data={"file": f}, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            doc = serializer.save(
                title=title_from_user or f.name,
                user=request.user,
            )
            created.append(doc)
            threading.Thread(
                target=run_processing, args=(doc.id,), daemon=True
            ).start()

        data = DocumentSerializer(
            created, many=True, context={"request": request}
        ).data

        if single_old_way:
            return Response(data[0], status=status.HTTP_201_CREATED)
        return Response(data, status=status.HTTP_201_CREATED)

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