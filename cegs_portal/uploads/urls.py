from django.urls import path

from . import views

app_name = "uploads"
urlpatterns = [
    path("", views.upload, name="upload"),
]
