from django.urls import path

from . import views

app_name = "task_status"
urlpatterns = [
    path("<username>", views.TaskStatusView.as_view(), name="task_status"),
]
