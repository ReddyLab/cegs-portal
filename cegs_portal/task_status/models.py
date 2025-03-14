import uuid

from django.conf import settings
from django.db import models


class TaskStatus(models.Model):
    class TaskState(models.TextChoices):
        WAITING = "W", "Waiting to Begin"
        STARTED = "S", "Started"
        FINISHED = "F", "Finished"
        ERROR = "E", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="tasks")
    status = models.CharField(max_length=1, choices=TaskState.choices, default=TaskState.WAITING)
    description = models.CharField(max_length=512, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def start(self):
        self.status = self.TaskState.STARTED
        self.save()

    def finish(self):
        if self.status != self.TaskState.ERROR:
            self.status = self.TaskState.FINISHED
            self.save()

    def error(self, error_message):
        self.status = self.TaskState.ERROR
        self.error_message = error_message
        self.save()

    def __str__(self):
        return f"{self.description} Status: {self.get_status_display()} Created: {self.created} Modified: {self.modified} ({self.id})"
