from django.urls import path

from . import views

app_name = "uploads"
urlpatterns = [
    path("", views.upload, name="upload"),
    path("upload_complete", views.upload_complete, name="upload_complete"),
]
