from django.urls import path
from . import views
from .views import improve_generate_image


urlpatterns = [
    path("", views.improve_view, name="improve"),
    path("analyze/", views.improve_analyze, name="improve_analyze"),
    path("generate-image/", improve_generate_image, name="generate_image"),

]
