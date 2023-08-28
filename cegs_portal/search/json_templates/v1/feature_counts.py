from typing import Any, Optional, TypedDict

from cegs_portal.search.views.v1.search_types import FeatureCountResult

FeatureCountDict = TypedDict(
    "FeatureCount",
    {
        "feature_type": str,
        "count": int,
    },
)

FeatureCountJson = TypedDict(
    "FeatureCountJson",
    {
        "region": TypedDict("Region", {"chromo": str, "start": int, "end": int}),
        "assembly": str,
        "counts": list[FeatureCountDict],
    },
)


def feature_counts(
    feature_count_list: FeatureCountResult, _options: Optional[dict[str, Any]] = None
) -> FeatureCountJson:
    region = feature_count_list["region"]
    return {
        "region": {"chromo": region.chromo, "start": region.range.lower, "end": region.range.upper},
        "assembly": feature_count_list["assembly"],
        "counts": [
            {"feature_type": feature_type, "count": count} for feature_type, count in feature_count_list["counts"]
        ],
    }
