from typing import TypedDict

from cegs_portal.search.models import ChromosomeLocation

Loc = tuple[str, int, int]

FeatureCountResult = TypedDict(
    "FeatureCountResult",
    {
        "region": ChromosomeLocation,
        "assembly": str,
        "counts": list[tuple[str, int, int]],
    },
)
