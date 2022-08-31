from enum import Enum

from django.db import models

from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.dna_feature import DNAFeature
from cegs_portal.search.models.experiment import Experiment
from cegs_portal.search.models.facets import Faceted
from cegs_portal.search.models.searchable import Searchable


class EffectObservationDirectionType(Enum):
    DEPLETED = "Depleted Only"
    ENRICHED = "Enriched Only"
    NON_SIGNIFICANT = "Non-significant"
    BOTH = "Mixed"


class RegulatoryEffectObservationSet(models.QuerySet):
    def with_facet_values(self):
        return self.prefetch_related("facet_values")


class RegulatoryEffectObservation(Accessioned, Searchable, Faceted):
    class Meta(Accessioned.Meta, Searchable.Meta):
        indexes = [
            models.Index(fields=["accession_id"], name="re_accession_id_index"),
        ]

    class Facet(Enum):
        DIRECTION = "Direction"  # EffectObservationDirectionType
        RAW_P_VALUE = "Raw p value"  # float
        SIGNIFICANCE = "Significance"  # float
        EFFECT_SIZE = "Effect Size"  # float

    objects = RegulatoryEffectObservationSet.as_manager()

    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    sources = models.ManyToManyField(DNAFeature, related_name="source_for")
    targets = models.ManyToManyField(DNAFeature, related_name="target_of")

    @property
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
    def raw_p_value(self):
        return self.facet_num_values[RegulatoryEffectObservation.Facet.RAW_P_VALUE.value]

    def __str__(self):
        return f"{self.direction}: {self.sources.count()} source(s) -> {self.effect_size} on {self.targets.count()} target(s)"  # noqa: E501
