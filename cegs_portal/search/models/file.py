from django.db import models

from cegs_portal.search.models.facets import Faceted


class FileCategory(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=512, null=True, blank=True)


class File(Faceted):
    filename = models.CharField(max_length=512)
    location = models.CharField(max_length=2048)
    description = models.CharField(max_length=4096, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    experiment = models.ForeignKey(
        "Experiment",
        to_field="accession_id",
        db_column="experiment_accession_id",
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
    )
    analysis = models.ForeignKey("Analysis", on_delete=models.CASCADE, related_name="files", null=True, blank=True)
    size = models.PositiveBigIntegerField(null=True, blank=True)
    category = models.ForeignKey(FileCategory, on_delete=models.SET_NULL, null=True, blank=True)
    misc = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.filename}"
