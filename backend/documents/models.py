from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/")
    status = models.CharField(max_length=20, default="processing")  # processing / ready / failed
    warnings = models.JSONField(default=list, blank=True)
    pages = models.IntegerField(null=True, blank=True)
    chunks = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title