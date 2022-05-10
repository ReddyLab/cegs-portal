from django.db import models


class Searchable(models.Model):
    class Meta:
        abstract = True

    searchable = models.BooleanField(default=True, db_index=True)
