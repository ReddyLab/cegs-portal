from django.db import models


class Searchable(models.Model):
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["searchable"], name="%(class)s_srchbl_idx"),
        ]

    searchable = models.BooleanField(default=True)
