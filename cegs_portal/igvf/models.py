from django.db import models

from cegs_portal.search.models.validators import validate_accession_id


class QueryCache(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    value = models.JSONField(null=True, blank=True)
    experiment_accession_id = models.CharField(max_length=17, validators=[validate_accession_id], null=True, blank=True)
