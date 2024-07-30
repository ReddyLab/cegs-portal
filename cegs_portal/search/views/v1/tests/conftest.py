from typing import Iterable

import pytest
from psycopg2.extras import NumericRange

from cegs_portal.get_expr_data.conftest import reg_effects  # noqa: F401
from cegs_portal.search.models import (
    DNAFeature,
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


def _dna_features(assembly) -> Iterable[DNAFeature]:
    direction_facet = FacetFactory(description="", name=RegulatoryEffectObservation.Facet.DIRECTION.value)
    enriched_facet = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.ENRICHED.value)
    f1 = DNAFeatureFactory(
        parent=None,
        feature_type=DNAFeatureType.GENE,
        chrom_name="chr1",
        location=NumericRange(1, 100),
        ref_genome=assembly,
    )
    f2 = DNAFeatureFactory(
        parent=None,
        feature_type=DNAFeatureType.GENE,
        chrom_name="chr1",
        location=NumericRange(200, 300),
        ref_genome=assembly,
    )
    f3 = DNAFeatureFactory(
        parent=None,
        feature_type=DNAFeatureType.CCRE,
        chrom_name="chr1",
        location=NumericRange(1000, 2000),
        ref_genome=assembly,
    )
    f4 = DNAFeatureFactory(
        parent=None,
        feature_type=DNAFeatureType.CAR,
        chrom_name="chr1",
        location=NumericRange(50_000, 60_000),
        ref_genome=assembly,
    )
    f5 = DNAFeatureFactory(
        parent=None,
        feature_type=DNAFeatureType.CAR,
        chrom_name="chr1",
        location=NumericRange(70_000, 80_000),
        ref_genome=assembly,
    )
    sig_reo_source1 = RegEffectFactory(
        sources=[f5],
        facet_values=[enriched_facet],
    )
    sig_reo_source2 = RegEffectFactory(
        sources=[f4],
        facet_values=[enriched_facet],
    )
    sig_reo_target1 = RegEffectFactory(
        targets=[f1],
        facet_values=[enriched_facet],
    )
    return [f1, f2, f3, f4, f5, sig_reo_source1, sig_reo_source2, sig_reo_target1]


@pytest.fixture
def dna_features() -> Iterable[DNAFeature]:
    return _dna_features("hg38")


@pytest.fixture
def dna_features_hg19() -> Iterable[DNAFeature]:
    return _dna_features("hg19")
