from django.urls import path
from .views import (
    ChatView,
    GenerateView,
    StartQuizView,
    SubmitQuizView,
    ReviewQuizView,
    AttemptHistoryView,
)

urlpatterns = [
    path("chat/", ChatView.as_view()),
    path("quiz/generate/", GenerateView.as_view()),
    path("quiz/start/", StartQuizView.as_view()),
    path("quiz/attempts/", AttemptHistoryView.as_view()),
    path("quiz/<int:attempt_id>/submit/", SubmitQuizView.as_view()),
    path("quiz/<int:attempt_id>/review/", ReviewQuizView.as_view()),
]