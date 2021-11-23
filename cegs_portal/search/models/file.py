from django.db import models

from cegs_portal.search.models.facets import FacetedModel


class File(FacetedModel):
    filename = models.CharField(max_length=512)
    description = models.CharField(max_length=4096, null=True)
    url = models.CharField(max_length=2048, null=True)
