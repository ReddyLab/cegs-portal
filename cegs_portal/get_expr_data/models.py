from django.conf import settings
from django.db import models


class ExperimentData(models.Model):
    class DataState(models.TextChoices):
        IN_PREPARATION = "IN_PREP", "In Preparation"
        READY = "READY", "Ready"
        DELETED = "DELETED", "Deleted"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.CharField(max_length=8, choices=DataState.choices, default=DataState.IN_PREPARATION)
    data = models.FileField(upload_to="expr_data")
