from datetime import datetime, timezone

from django.db import models


class TaskException(Exception):
    pass


# ThreadTask model based on https://github.com/nbwoodward/django-async-threading
class ThreadTask(models.Model):
    description = models.CharField(max_length=140, blank=True, null=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    is_done = models.BooleanField(blank=False, default=False)
    failed = models.BooleanField(blank=False, default=False)
    failed_exception = models.CharField(max_length=1024, blank=True, null=True)

    @classmethod
    def new(cls, description=None):
        task = cls(description=description, started_at=datetime.now(timezone.utc))
        return task

    def set_description(self, description):
        self.description = description
        self.save()

    def end(self):
        self.ended_at = datetime.now(timezone.utc)
        self.is_done = True
        self.save()

    def fail(self, reason):
        self.ended_at = datetime.now(timezone.utc)
        self.is_done = True
        self.failed = True
        self.failed_exception = reason
        self.save()

    @property
    def display_name(self):
        if self.description is not None:
            return f"Task {self.id}: {self.description[:20]}..."

        return f"Task {self.id}: [No Description]"

    def __str__(self):
        return self.display_name
