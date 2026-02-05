from django.urls import path
from . import views

urlpatterns = [
    path("", views.improve_view, name="improve"),
    path("analyze/", views.improve_analyze, name="improve_analyze"),
]
