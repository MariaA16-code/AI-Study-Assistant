from django.urls import path

from .views import ChatView, GenerateView

urlpatterns = [
    path("chat/", ChatView.as_view()),
    path("quiz/generate/", GenerateView.as_view()),
]