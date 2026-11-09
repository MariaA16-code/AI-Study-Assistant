import os
from rest_framework import serializers
from .models import Document

ALLOWED = {".pdf", ".docx", ".txt"}
MAX_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_FILES = 10  # files per upload request


def validate_upload(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED:
        raise serializers.ValidationError("Only PDF, DOCX and TXT files are allowed.")
    if f.size > MAX_SIZE:
        raise serializers.ValidationError("File is too large (max 25 MB).")
    return f


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file", "status", "warnings", "pages", "chunks", "created_at"]
        read_only_fields = ["id", "status", "warnings", "pages", "chunks", "created_at"]
        extra_kwargs = {"title": {"required": False}}

    def validate_file(self, f):
        return validate_upload(f)


class DocumentUploadSerializer(serializers.Serializer):
    """Used only to show the upload form on /api/docs/."""
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        help_text="One or more files (PDF, DOCX, TXT, max 25 MB each, up to 10 files).",
    )
    file = serializers.FileField(required=False, help_text="Single file (old way).")
    title = serializers.CharField(required=False, help_text="Only used when one file is sent.")