from django.urls import path
from . import views

urlpatterns = [
    path("", views.forge_intro, name="forge"),
    path("brainstorm/", views.forge_brainstorm, name="forge_brainstorm"),
    path("plan/", views.forge_plan, name="forge_plan"),

    # API endpoints for scoring/recommendations
    path("brainstorm/evaluate/", views.forge_brainstorm_evaluate, name="forge_brainstorm_evaluate"),
    path("plan/evaluate/", views.forge_plan_evaluate, name="forge_plan_evaluate"),
]
