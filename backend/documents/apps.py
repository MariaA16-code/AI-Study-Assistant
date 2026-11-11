import sys
import threading

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'

    def ready(self):
        # load the AI model only when the server runs, not for migrate etc.
        if "runserver" not in sys.argv:
            return
        import ai_service

        warm_up = getattr(ai_service, "warm_up", None)
        if warm_up:
            threading.Thread(target=warm_up, daemon=True).start()