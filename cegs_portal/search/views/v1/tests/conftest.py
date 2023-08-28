from typing import Iterable

import pytest
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, DNAFeatureType
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory


def _dna_features(assembly) -> Iterable[DNAFeature]:
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
    return [f1, f2, f3, f4, f5]


@pytest.fixture
def dna_features() -> Iterable[DNAFeature]:
    return _dna_features("GRCh38")


@pytest.fixture
def dna_features_grch37() -> Iterable[DNAFeature]:
    return _dna_features("GRCh37")
