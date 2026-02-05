from django.urls import path
from . import views

urlpatterns = [
    path("", views.videoscript_view, name="videoscript"),
    path("generate/", views.videoscript_generate, name="videoscript_generate"),
    path("download/", views.videoscript_download, name="videoscript_download"),
]
