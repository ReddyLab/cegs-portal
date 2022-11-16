from django.db import models

from cegs_portal.search.models.facets import Faceted


class File(Faceted):
    filename = models.CharField(max_length=512)
    description = models.CharField(max_length=4096, null=True, blank=True)
    url = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return f"{self.filename}"
