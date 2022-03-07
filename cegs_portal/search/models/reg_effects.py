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
    # Facets:
    #  * Direction (Discrete, EffectDirectionType)
    #  * Raw p value (Continuous, float)
    #  * Signficance (Continuous, float)
    #  * Effect Size (Continuous, float)

    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    sources = models.ManyToManyField(DNARegion, related_name="regulatory_effects")
    targets = models.ManyToManyField(Feature, related_name="regulatory_effects")
    target_assemblies = models.ManyToManyField(FeatureAssembly, related_name="regulatory_effects")

    def __str__(self):
        direction = self.facet_values.get(facet__name="Direction")
        effect_size = self.facet_values.get(facet__name="Effect Size")
        return f"{direction.value}: {self.sources.count()} source(s) -> {effect_size.num_value} on {self.targets.count()} target(s)"  # noqa: E501
