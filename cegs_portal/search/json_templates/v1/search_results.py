from typing import Any, Optional, TypedDict

from django.db.models import Manager

from cegs_portal.search.json_templates.v1.dna_features import features
from cegs_portal.search.models import DNAFeature, Facet
from cegs_portal.utils.pagination_types import Pageable

Location = TypedDict("Location", {"assembly": str, "chromosome": str, "start": int, "end": int})
SearchResults = TypedDict(
    "SearchResults", {"location": Location, "features": Pageable[DNAFeature], "facets": Manager[Facet]}
)


def search_results(results: SearchResults, options: Optional[dict[str, Any]] = None):
    response = {
        "features": features(results["features"], options),
        "facets": [
            {"name": f.name, "description": f.description, "values": [value.value for value in f.values.all()]}
            for f in results["facets"].all()
        ],
    }

    if results["location"] is not None:
        response["location"] = {
            "assembly": results["assembly"],
            "chromosome": results["location"].chromo,
            "start": results["location"].range.lower,
            "end": results["location"].range.upper,
        }

    return response
