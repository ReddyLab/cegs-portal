import pytest

from cegs_portal.search.models import (
    DNAFeatureType,
    EffectObservationDirectionType,
    RegulatoryEffectObservation,
)
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.facet_factory import (
    FacetFactory,
    FacetValueFactory,
)
from cegs_portal.search.models.tests.reg_effects_factory import RegEffectFactory


@pytest.fixture
def proximal_non_targeting_reg_effects():
    gene = DNAFeatureFactory(feature_type=DNAFeatureType.GENE)
    source = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, closest_gene=gene)

    direction_facet = FacetFactory(description="", name=RegulatoryEffectObservation.Facet.DIRECTION.value)

    direction_enriched = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.ENRICHED.value)
    direction_depleted = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.DEPLETED.value)
    direction_non_significant = FacetValueFactory(
        facet=direction_facet, value=EffectObservationDirectionType.NON_SIGNIFICANT.value
    )

    reo1 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_enriched,),
    )
    reo2 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_depleted,),
    )
    reo3 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_non_significant,),
    )
    reo4 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_non_significant,),
    )

    return {
        "source": source,
        "effects": [reo1, reo2, reo3, reo4],
    }


@pytest.fixture
def private_proximal_non_targeting_reg_effects():
    private_gene = DNAFeatureFactory(feature_type=DNAFeatureType.GENE, public=False)
    source = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, closest_gene=private_gene)

    direction_facet = FacetFactory(description="", name=RegulatoryEffectObservation.Facet.DIRECTION.value)

    direction_enriched = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.ENRICHED.value)
    direction_depleted = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.DEPLETED.value)
    direction_non_significant = FacetValueFactory(
        facet=direction_facet, value=EffectObservationDirectionType.NON_SIGNIFICANT.value
    )

    reo1 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_enriched,),
    )
    reo2 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_depleted,),
    )
    reo3 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_non_significant,),
    )
    reo4 = RegEffectFactory(
        sources=(source,),
        facet_values=(direction_non_significant,),
    )

    return {
        "source": source,
        "effects": [reo1, reo2, reo3, reo4],
    }
