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


class RegulatoryEffect(Searchable, FacetedModel):
    DIRECTION_CHOICES = [
        (EffectDirectionType.DEPLETED, "depleted"),  # significance < 0.01, effect size -
        (EffectDirectionType.ENRICHED, "enriched"),  # significance < 0.01, effect size +
        (EffectDirectionType.BOTH, "both"),
        (EffectDirectionType.NON_SIGNIFICANT, "non_sig"),  # significance >= 0.01 or value = 0
    ]
    direction = models.CharField(
        max_length=8,
        choices=DIRECTION_CHOICES,
        default=EffectDirectionType.NON_SIGNIFICANT,
    )
    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    effect_size = models.FloatField(null=True)  # log2 fold changes
    significance = models.FloatField(null=True)  # an adjusted p value
    raw_p_value = models.FloatField(null=True)  # p value, scaled with -log10
    sources = models.ManyToManyField(DNARegion, related_name="regulatory_effects")
    targets = models.ManyToManyField(Feature, related_name="regulatory_effects")
    target_assemblies = models.ManyToManyField(FeatureAssembly, related_name="regulatory_effects")

    def __str__(self):
        return f"{self.direction}: {self.sources.count()} source(s) -> {self.effect_size} on {self.targets.count()} target(s)"  # noqa: E501
