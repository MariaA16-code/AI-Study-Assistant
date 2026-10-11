from django.db import models
from documents.models import Document


class QuizAttempt(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="attempts"
    )
    question_type = models.CharField(max_length=10)
    difficulty = models.CharField(max_length=10)
    questions = models.JSONField(default=list)   # full questions incl. correct_index
    answers = models.JSONField(default=dict, blank=True)  # {"0": 2, "1": 0}
    score = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attempt {self.id} on document {self.document_id}"