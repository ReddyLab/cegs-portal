from django.db import models

from cegs_portal.search.models.validators import validate_accession_id


class Accessioned(models.Model):
    class Meta:
        abstract = True

    class Facets:
        pass

    accession_id = models.CharField(max_length=12, validators=[validate_accession_id], null=True, unique=True)
