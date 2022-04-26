from enum import Enum
from re import fullmatch

from django.core.exceptions import ValidationError
from django.db import models

from cegs_portal.search.models.facets import FacetedModel
from cegs_portal.search.models.file import File


class CellLine(models.Model):
    line_name = models.CharField(max_length=100)

    def __str__(self):
        return self.line_name


class TissueType(models.Model):
    tissue_type = models.CharField(max_length=100)

    def __str__(self):
        return self.tissue_type


def validate_accession_id(value):
    if value is not None and fullmatch("DCPE[0-9A-Z]{4}", value) is None:
        raise ValidationError(f'{value} is not of the form "DCPEXXXX", where X is a number or capital letter')


class Experiment(FacetedModel):
    class Facet(Enum):
        ASSAYS = "Experiment Assays"

    archived = models.BooleanField(default=False)
    description = models.CharField(max_length=4096, null=True)
    experiment_type = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=512)
    other_files = models.ManyToManyField(File, related_name="experiments")
    accession_id = models.CharField(max_length=8, validators=[validate_accession_id], null=True, unique=True)

    def assay(self):
        return self.facet_values.get(facet__name=Experiment.Facet.ASSAYS.value).value

    def __str__(self):
        return f"{self.id}: {self.name} ({self.experiment_type})"


class ExperimentDataFile(models.Model):
    cell_line = models.CharField(max_length=100)
    cell_lines = models.ManyToManyField(CellLine, related_name="experiment_data")
    description = models.CharField(max_length=4096, null=True)
    experiment = models.ForeignKey("Experiment", on_delete=models.CASCADE, related_name="data_files")
    filename = models.CharField(max_length=512)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)
    significance_measure = models.CharField(max_length=2048)
    tissue_types = models.ManyToManyField(TissueType, related_name="experiment_data")

    def __str__(self):
        return f"{self.filename}:\n{self.description}"
