from enum import Enum

from django.contrib.postgres.fields import DateRangeField
from django.db import models

from cegs_portal.search.models.access_control import AccessControlled
from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.dna_feature_type import DNAFeatureSourceType
from cegs_portal.search.models.facets import Faceted
from cegs_portal.search.models.file import File


class TissueType(Accessioned):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=4096, null=True, blank=True)

    def __str__(self):
        return self.name


class CellLine(Accessioned):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=4096, null=True, blank=True)
    tissue_type = models.ForeignKey(TissueType, on_delete=models.PROTECT)
    tissue_type_name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Biosample(Accessioned):
    name = models.CharField(max_length=100, null=True, blank=True)
    cell_line = models.ForeignKey(CellLine, on_delete=models.PROTECT)
    cell_line_name = models.CharField(max_length=100)
    description = models.CharField(max_length=4096, null=True, blank=True)
    misc = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.cell_line_name})"


class Experiment(Accessioned, Faceted, AccessControlled):
    class Meta(Accessioned.Meta):
        indexes = [
            models.Index(fields=["accession_id"], name="exp_accession_id_index"),
        ]

    class Facet(Enum):
        ASSAYS = "Experiment Assays"
        SOURCE_TYPES = "Experiment Source Type"
        CELL_LINE = "Cell Line"
        TISSUE_TYPE = "Tissue Type"

    description = models.CharField(max_length=4096, null=True, blank=True)
    experiment_type = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=512)
    biosamples = models.ManyToManyField(Biosample, related_name="experiments", blank=True)
    other_files = models.ManyToManyField(File, related_name="experiments", blank=True)
    source_type = models.CharField(
        max_length=50, choices=DNAFeatureSourceType.choices, default=DNAFeatureSourceType.GRNA
    )
    default_analysis = models.ForeignKey(
        "Analysis", on_delete=models.SET_NULL, blank=True, null=True, related_name="default_for"
    )

    def assay(self):
        return self.facet_values.get(facet__name=Experiment.Facet.ASSAYS.value).value

    def __str__(self):
        return f"{self.accession_id}: {self.name} ({self.experiment_type})"


# Deprecated in favor of File + ExperimentDataFileInfo
class ExperimentDataFile(models.Model):
    description = models.CharField(max_length=4096, null=True, blank=True)
    experiment = models.ForeignKey("Experiment", on_delete=models.CASCADE, related_name="data_files")
    filename = models.CharField(max_length=512)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10, blank=True)
    significance_measure = models.CharField(max_length=2048)

    def __str__(self):
        return f"{self.experiment.accession_id}: {self.filename}"


class ExperimentDataFileInfo(models.Model):
    ref_genome = models.CharField(max_length=20, blank=True)
    ref_genome_patch = models.CharField(max_length=10, null=True, blank=True)
    significance_measure = models.CharField(max_length=2048, blank=True)
    p_value_threshold = models.FloatField(default=0.05, blank=True)

    def __str__(self):
        if self.ref_genome_patch is not None and self.ref_genome_patch != "":
            return f"ref genome: {self.ref_genome}.{self.ref_genome_patch}, p_val_threshold: {self.p_value_threshold}"

        return f"ref genome: {self.ref_genome}, p_val_threshold: {self.p_value_threshold}"


class Analysis(Accessioned, Faceted, AccessControlled):
    class Meta(Accessioned.Meta):
        indexes = [
            models.Index(fields=["accession_id"], name="an_accession_id_index"),
        ]
        verbose_name_plural = "Analyses"

    name = models.CharField(max_length=512)
    description = models.CharField(max_length=4096, blank=True)
    experiment = models.ForeignKey(
        "Experiment",
        to_field="accession_id",
        db_column="experiment_accession_id",
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    when = DateRangeField(null=True, blank=True)

    def __str__(self):
        description = self.description

        if len(description) > 15:
            return f"{self.accession_id}: {description[:15]}..."

        return f"{self.accession_id}: {description}"


class Pipeline(models.Model):
    analysis = models.ForeignKey("Analysis", on_delete=models.CASCADE, related_name="pipelines")
    description = models.CharField(max_length=4096)
    url = models.URLField(null=True, blank=True)
