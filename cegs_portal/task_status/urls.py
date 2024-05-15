from django.urls import path

from . import views

app_name = "task_status"
urlpatterns = [
    path("task/<uuid:task_id>", views.TaskStatusView.as_view(), name="task_status"),
    path("<username>", views.TaskStatusListView.as_view(), name="task_status_list"),
]
