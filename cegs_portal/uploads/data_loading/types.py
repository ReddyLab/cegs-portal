from enum import StrEnum

from cegs_portal.search.models import (
    DNAFeature,
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
    CRE = DNAFeatureType.CRE.value
    GE = DNAFeatureType.GE.value


class Facets(StrEnum):
    DIRECTION = RegulatoryEffectObservation.Facet.DIRECTION.value
    RAW_P_VALUE = RegulatoryEffectObservation.Facet.RAW_P_VALUE.value
    SIGNIFICANCE = RegulatoryEffectObservation.Facet.SIGNIFICANCE.value
    LOG_SIGNIFICANCE = RegulatoryEffectObservation.Facet.LOG_SIGNIFICANCE.value
    EFFECT_SIZE = RegulatoryEffectObservation.Facet.EFFECT_SIZE.value
    AVG_COUNTS_PER_MILLION = RegulatoryEffectObservation.Facet.AVG_COUNTS_PER_MILLION.value
    ASSAYS = DNAFeature.Facet.ASSAYS.value
    CCRE_CATEGORIES = DNAFeature.Facet.CCRE_CATEGORIES.value
    DHS_CCRE_OVERLAP_CATEGORIES = DNAFeature.Facet.DHS_CCRE_OVERLAP_CATEGORIES.value
    GRNA_TYPE = DNAFeature.Facet.GRNA_TYPE.value
    PROMOTER = DNAFeature.Facet.PROMOTER.value


class DirectionFacets(StrEnum):
    DEPLETED = EffectObservationDirectionType.DEPLETED.value
    ENRICHED = EffectObservationDirectionType.ENRICHED.value
    NON_SIGNIFICANT = EffectObservationDirectionType.NON_SIGNIFICANT.value
    BOTH = EffectObservationDirectionType.BOTH.value


class GenomeAssembly(StrEnum):
    GRCH38 = "GRCh38"
    GRCH37 = "GRCh37"
    HG19 = "hg19"
    HG38 = "hg38"


class ChromosomeStrands(StrEnum):
    POSITIVE = "+"
    NEGATIVE = "-"
