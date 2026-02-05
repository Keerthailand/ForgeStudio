from django.urls import path
from . import views

urlpatterns = [
    path("", views.posting_view, name="posting"),
    path("generate/", views.posting_generate, name="posting_generate"),
]
