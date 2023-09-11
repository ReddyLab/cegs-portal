from cegs_portal.search.json_templates.v1.feature_counts import (
    feature_counts as fc_json,
)
from cegs_portal.search.views.v1.search_types import FeatureCountResult


def test_feature_counts(feature_count_result: FeatureCountResult):
    region = feature_count_result["region"]
    assert fc_json(feature_count_result) == {
        "region": {"chromo": region.chromo, "start": region.range.lower, "end": region.range.upper},
        "assembly": feature_count_result["assembly"],
        "counts": [
            {"feature_type": feature_type, "count": count, "sig_reo_count": sig_reo_count}
            for feature_type, count, sig_reo_count in feature_count_result["feature_counts"]
        ],
    }
