from typing import Any, Optional, TypedDict

from django.db.models import Manager

from cegs_portal.search.json_templates.v1.dna_features import features
from cegs_portal.search.models import DNAFeature, Facet
from cegs_portal.search.models.utils import ChromosomeLocation
from cegs_portal.utils.pagination_types import Pageable

Location = TypedDict("Location", {"location": ChromosomeLocation, "assembly": str})
SearchResults = TypedDict(
    "SearchResults", {"loc_search": Location, "dhss": Pageable[DNAFeature], "facets": Manager[Facet]}
)


def search_results(results: SearchResults, options: Optional[dict[str, Any]] = None):
    return {
        "location": {
            "assembly": results["loc_search"]["assembly"],
            "chromosome": results["loc_search"]["location"].chromo,
            "start": results["loc_search"]["location"].range.lower,
            "end": results["loc_search"]["location"].range.upper,
        },
        "features": features(results["dhss"], options),
        "facets": [
            {"name": f.name, "description": f.description, "values": [value.value for value in f.values.all()]}
            for f in results["facets"].all()
        ],
    }
