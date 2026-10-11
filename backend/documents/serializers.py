import os
from rest_framework import serializers
from .models import Document

ALLOWED = {".pdf", ".docx", ".txt"}
MAX_SIZE = 25 * 1024 * 1024  # 25 MB


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file", "status", "warnings", "pages", "chunks", "created_at"]
        read_only_fields = ["id", "status", "warnings", "pages", "chunks", "created_at"]
        extra_kwargs = {"title": {"required": False}}

    def validate_file(self, f):
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED:
            raise serializers.ValidationError("Only PDF, DOCX and TXT files are allowed.")
        if f.size > MAX_SIZE:
            raise serializers.ValidationError("File is too large (max 25 MB).")
        return f