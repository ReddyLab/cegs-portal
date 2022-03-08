from enum import Enum

from django.db import models

from cegs_portal.search.models.dna_region import DNARegion
from cegs_portal.search.models.experiment import Experiment
from cegs_portal.search.models.facets import FacetedModel
from cegs_portal.search.models.features import Feature, FeatureAssembly
from cegs_portal.search.models.searchable import Searchable


class EffectDirectionType(Enum):
    DEPLETED = "depleted"
    ENRICHED = "enriched"
    NON_SIGNIFICANT = "non_sig"
    BOTH = "both"


class RegulatoryEffectSet(models.QuerySet):
    def with_facet_values(self):
        return self.prefetch_related("facet_values")


class RegulatoryEffect(Searchable, FacetedModel):
    class Facet(Enum):
        DIRECTION = "Direction"  # EffectDirectionType
        RAW_P_VALUE = "Raw p value"  # float
        SIGNIFICANCE = "Significance"  # float
        EFFECT_SIZE = "Effect Size"  # float

    objects = RegulatoryEffectSet.as_manager()

    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    sources = models.ManyToManyField(DNARegion, related_name="regulatory_effects")
    targets = models.ManyToManyField(Feature, related_name="regulatory_effects")
    target_assemblies = models.ManyToManyField(FeatureAssembly, related_name="regulatory_effects")

    @property
    def direction(self):
        return self.facet_values.get(facet__name=RegulatoryEffect.Facet.DIRECTION.value).value

    @property
    def effect_size(self):
        return self.facet_values.get(facet__name=RegulatoryEffect.Facet.EFFECT_SIZE.value).num_value

    @property
    def significance(self):
        return self.facet_values.get(facet__name=RegulatoryEffect.Facet.SIGNIFICANCE.value).num_value

    @property
    def raw_p_value(self):
        return self.facet_values.get(facet__name=RegulatoryEffect.Facet.RAW_P_VALUE.value).num_value

    def __str__(self):
        return f"{self.direction.value}: {self.sources.count()} source(s) -> {self.effect_size.num_value} on {self.targets.count()} target(s)"  # noqa: E501
