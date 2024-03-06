from enum import StrEnum

from cegs_portal.search.models import (
    DNAFeatureType,
    EffectObservationDirectionType,
    GrnaType,
    PromoterType,
    RegulatoryEffectObservation,
)


class GrnaFacet(StrEnum):
    POSITIVE_CONTROL = GrnaType.POSITIVE_CONTROL.value
    NEGATIVE_CONTROL = GrnaType.NEGATIVE_CONTROL.value
    TARGETING = GrnaType.TARGETING.value


class PromoterFacet(StrEnum):
    PROMOTER = PromoterType.PROMOTER.value
    NON_PROMOTER = PromoterType.NON_PROMOTER.value


class FeatureType(StrEnum):
    GENE = DNAFeatureType.GENE.value
    TRANSCRIPT = DNAFeatureType.TRANSCRIPT.value
    EXON = DNAFeatureType.EXON.value
    CCRE = DNAFeatureType.CCRE.value
    DHS = DNAFeatureType.DHS.value
    GRNA = DNAFeatureType.GRNA.value
    CAR = DNAFeatureType.CAR.value


class NumericFacets(StrEnum):
    EFFECT_SIZE = RegulatoryEffectObservation.Facet.EFFECT_SIZE.value
    SIGNIFICANCE = RegulatoryEffectObservation.Facet.SIGNIFICANCE.value
    LOG_SIGNIFICANCE = RegulatoryEffectObservation.Facet.LOG_SIGNIFICANCE.value
    RAW_P_VALUE = RegulatoryEffectObservation.Facet.RAW_P_VALUE.value
    AVG_COUNTS_PER_MILLION = RegulatoryEffectObservation.Facet.AVG_COUNTS_PER_MILLION.value


class DirectionFacets(StrEnum):
    DEPLETED = EffectObservationDirectionType.DEPLETED.value
    ENRICHED = EffectObservationDirectionType.ENRICHED.value
    NON_SIGNIFICANT = EffectObservationDirectionType.NON_SIGNIFICANT.value
    BOTH = EffectObservationDirectionType.BOTH.value
