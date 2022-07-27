from enum import Enum

from django.db import models

from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.dna_feature import DNAFeature
from cegs_portal.search.models.experiment import Experiment
from cegs_portal.search.models.facets import Faceted
from cegs_portal.search.models.searchable import Searchable


class EffectDirectionType(Enum):
    DEPLETED = "Depleted Only"
    ENRICHED = "Enriched Only"
    NON_SIGNIFICANT = "Non-significant"
    BOTH = "Mixed"


class RegulatoryEffectSet(models.QuerySet):
    def with_facet_values(self):
        return self.prefetch_related("facet_values")


class RegulatoryEffect(Accessioned, Searchable, Faceted):
    class Facet(Enum):
        DIRECTION = "Direction"  # EffectDirectionType
        RAW_P_VALUE = "Raw p value"  # float
        SIGNIFICANCE = "Significance"  # float
        EFFECT_SIZE = "Effect Size"  # float

    objects = RegulatoryEffectSet.as_manager()

    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    sources = models.ManyToManyField(DNAFeature, related_name="source_for")
    target_assemblies = models.ManyToManyField(DNAFeature, related_name="target_of")

    @property
    def direction(self):
        return self.facet_values.get(facet__name=RegulatoryEffect.Facet.DIRECTION.value).value

    @property
    def direction_id(self):
        return self.facet_values.get(facet__name=RegulatoryEffect.Facet.DIRECTION.value).id

    @property
    def effect_size(self):
        return self.facet_num_values[RegulatoryEffect.Facet.EFFECT_SIZE.value]

    @property
    def significance(self):
        return self.facet_num_values[RegulatoryEffect.Facet.SIGNIFICANCE.value]

    @property
    def raw_p_value(self):
        return self.facet_num_values[RegulatoryEffect.Facet.RAW_P_VALUE.value]

    def __str__(self):
        return f"{self.direction}: {self.sources.count()} source(s) -> {self.effect_size} on {self.target_assemblies.count()} target(s)"  # noqa: E501
