from django.urls import path

from cegs_portal.tasks.views import TaskStatusView

app_name = "tasks"
urlpatterns = [
    path("task/<int:task_id>", view=TaskStatusView.as_view(), name="status"),
]
