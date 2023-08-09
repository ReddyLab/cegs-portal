from django.db import models


class AccessControlled(models.Model):
    class Meta:
        abstract = True

    archived = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
