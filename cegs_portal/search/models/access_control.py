from django.db import models


class AccessControlled(models.Model):
    class Meta:
        abstract = True

    class Facets:
        pass

    archived = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
