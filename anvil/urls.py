from django.urls import path
from . import views

urlpatterns = [
    path("", views.anvil_view, name="anvil"),
    path("chat/", views.anvil_chat, name="anvil_chat"),
    path("reset/", views.anvil_reset, name="anvil_reset"),
]
