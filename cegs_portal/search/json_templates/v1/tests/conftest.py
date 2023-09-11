import pytest

from cegs_portal.search.models import ChromosomeLocation, DNAFeatureType
from cegs_portal.search.views.v1.search_types import FeatureCountResult


@pytest.fixture
def feature_count_result() -> FeatureCountResult:
    return {
        "location": ChromosomeLocation("chr1", 1, 100_000),
        "assembly": "GRCh38",
        "feature_counts": [(DNAFeatureType.GENE, 12, 3), (DNAFeatureType.CCRE, 5, 0), ((DNAFeatureType.GRNA, 77, 13))],
    }
