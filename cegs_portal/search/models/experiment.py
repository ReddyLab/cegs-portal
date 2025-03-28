from enum import Enum, StrEnum

from django.contrib import admin
from django.contrib.postgres.fields import DateRangeField
from django.db import models

from cegs_portal.search.models.access_control import AccessControlled
from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.dna_feature_type import DNAFeatureSourceType
from cegs_portal.search.models.facets import Faceted
from cegs_portal.search.models.file import File

from .signals import update_analysis_access, update_experiment_access


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


# Really, this should be contained in the Experiment class, like Provenance
class FunctionalCharacterizationType(StrEnum):
    REPORTER_ASSAY = "Reporter Assay"
    CRISPRA = "CRISPRa"
    CRISPRI = "CRISPRi"


# Really, this should be contained in the Experiment class, like Provenance
class GenomeAssemblyType(StrEnum):
    HG19 = "hg19"
    HG38 = "hg38"


class Experiment(Accessioned, Faceted, AccessControlled):
    class Provenance(StrEnum):
        IGVF = "IGVF"
        CCGR = "CCGR"

    class Meta(Accessioned.Meta):
        indexes = [
            models.Index(fields=["accession_id"], name="exp_accession_id_index"),
        ]

    class Facet(Enum):
        ASSAYS = "Experiment Assays"
        SOURCE_TYPES = "Experiment Source Type"
        BIOSAMPLE = "Biosample"
        GENOME_ASSEMBLY = "Genome Assembly"  # GenomeAssemblyType
        FUNCTIONAL_CHARACTERIZATION = "Functional Characterization Modality"  # FunctionalCharacterizationType
        PROVENANCE = "Provenance"  # Provenance

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

    related_experiments = models.ManyToManyField(
        "Experiment", related_name="related", blank=True, through="ExperimentRelation"
    )

    def assay(self):
        return self.facet_values.get(facet__name=Experiment.Facet.ASSAYS.value).value

    def save(self, *args, **kwargs):
        update_access = kwargs.get("update_access", False)
        if "update_access" in kwargs:
            del kwargs["update_access"]
        super(Experiment, self).save(*args, **kwargs)
        if update_access:
            created = self.pk is None
            update_experiment_access(self, created)

    def __str__(self):
        return f"{self.accession_id}: {self.name} ({self.experiment_type})"


class ExperimentRelation(models.Model):
    this_experiment = models.ForeignKey(
        Experiment, to_field="accession_id", related_name="this", on_delete=models.CASCADE
    )
    other_experiment = models.ForeignKey(
        Experiment, to_field="accession_id", related_name="other", on_delete=models.CASCADE
    )
    description = models.CharField(max_length=4096, null=True, blank=True)

    @admin.display(description="From Experiment")
    def from_experiment(self):
        return f"{self.this_experiment.accession_id}: {self.this_experiment.name}"

    @admin.display(description="To Experiment")
    def to_experiment(self):
        return f"{self.other_experiment.accession_id}: {self.other_experiment.name}"


class ExperimentCollection(Accessioned, Faceted, AccessControlled):
    class Meta(Accessioned.Meta):
        indexes = [
            models.Index(fields=["accession_id"], name="expcol_accession_id_index"),
        ]

    name = models.CharField(max_length=512)
    description = models.CharField(max_length=4096, null=True, blank=True)
    experiments = models.ManyToManyField(Experiment, related_name="collections", blank=True)


class ExperimentSource(models.Model):
    pi = models.CharField(max_length=512, null=False)
    institution = models.CharField(max_length=512, null=False)
    experimentalist = models.CharField(max_length=512, blank=True, null=True)
    project = models.CharField(max_length=512, blank=True, null=True)
    datasource_url = models.URLField(blank=True, null=True)
    lab_url = models.URLField(blank=True, null=True)
    experiment = models.OneToOneField(Experiment, on_delete=models.CASCADE, related_name="attribution")


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
    genome_assembly = models.CharField(max_length=20)
    genome_assembly_patch = models.CharField(max_length=10, null=True, blank=True)
    p_value_threshold = models.FloatField(default=0.05)
    p_value_adj_method = models.CharField(max_length=128, default="unknown")

    def save(self, *args, **kwargs):
        super(Analysis, self).save(*args, **kwargs)
        if kwargs.get("update_access", False):
            created = self.pk is None
            update_analysis_access(self, created)

    def __str__(self):
        description = self.description

        if len(description) > 15:
            return f"{self.accession_id}: {description[:15]}..."

        return f"{self.accession_id}: {description}"


class Pipeline(models.Model):
    analysis = models.ForeignKey("Analysis", on_delete=models.CASCADE, related_name="pipelines")
    description = models.CharField(max_length=4096)
    url = models.URLField(null=True, blank=True)
