from enum import Enum
from functools import cached_property
from typing import Optional

from django.db import models

from cegs_portal.search.models.access_control import AccessControlled
from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.dna_feature import DNAFeature
from cegs_portal.search.models.experiment import Analysis, Experiment
from cegs_portal.search.models.facets import Faceted


class EffectObservationDirectionType(Enum):
    DEPLETED = "Depleted Only"
    ENRICHED = "Enriched Only"
    NON_SIGNIFICANT = "Non-significant"
    BOTH = "Mixed"


class RegulatoryEffectObservationSet(models.QuerySet):
    def with_facet_values(self):
        return self.prefetch_related("facet_values", "facet_values__facet")


class RegulatoryEffectObservation(Accessioned, Faceted, AccessControlled):
    class Meta(Accessioned.Meta):
        indexes = [
            models.Index(fields=["accession_id"], name="re_accession_id_index"),
        ]

    class Facet(Enum):
        DIRECTION = "Direction"  # EffectObservationDirectionType
        RAW_P_VALUE = "Raw p value"  # float
        SIGNIFICANCE = "Significance"  # float, adjusted p value
        LOG_SIGNIFICANCE = "-log10 Significance"  # float, -log10 adjusted p value
        EFFECT_SIZE = "Effect Size"  # float
        AVG_COUNTS_PER_MILLION = "Average Counts per Million"

    objects = RegulatoryEffectObservationSet.as_manager()

    name = models.CharField(max_length=100, unique=True, null=True, blank=True, default=None)
    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    experiment_accession = models.ForeignKey(
        Experiment,
        null=True,
        to_field="accession_id",
        db_column="experiment_accession_id",
        related_name="+",
        on_delete=models.CASCADE,
    )
    analysis = models.ForeignKey(
        Analysis,
        null=True,
        to_field="accession_id",
        db_column="analysis_accession_id",
        related_name="+",
        on_delete=models.CASCADE,
    )
    analysis_accession_id: Optional[str]
    sources = models.ManyToManyField(DNAFeature, related_name="source_for", blank=True)
    targets = models.ManyToManyField(DNAFeature, related_name="target_of", blank=True)

    @cached_property
    def direction(self):
        values = [
            value
            for value in self.facet_values.all()
            if value.facet.name == RegulatoryEffectObservation.Facet.DIRECTION.value
        ]
        return values[0].value if len(values) == 1 else None

    @property
    def direction_id(self):
        values = [
            value
            for value in self.facet_values.all()
            if value.facet.name == RegulatoryEffectObservation.Facet.DIRECTION.value
        ]
        return values[0].id if len(values) == 1 else None

    @property
    def effect_size(self):
        return self.facet_num_values[RegulatoryEffectObservation.Facet.EFFECT_SIZE.value]

    @property
    def significance(self):
        return self.facet_num_values[RegulatoryEffectObservation.Facet.SIGNIFICANCE.value]

    @property
    def log_significance(self):
        return self.facet_num_values[RegulatoryEffectObservation.Facet.LOG_SIGNIFICANCE.value]

    @property
    def raw_p_value(self):
        return self.facet_num_values[RegulatoryEffectObservation.Facet.RAW_P_VALUE.value]

    def __str__(self):
        return f"{self.accession_id}:  effect size: {self.effect_size}, significance: {self.significance}, p-val: {self.raw_p_value} from {self.experiment_accession_id}"  # noqa: E501
