from typing import Optional, TypedDict

from django.db.models import Manager

from cegs_portal.search.json_templates.v1.dna_region import dnaregions
from cegs_portal.search.models import DNARegion, Facet
from cegs_portal.search.models.utils import ChromosomeLocation
from cegs_portal.utils.pagination_types import Pageable

Location = TypedDict("Location", {"location": ChromosomeLocation, "assembly": str})
SearchResults = TypedDict(
    "SearchResults", {"loc_search": Location, "dhss": Pageable[DNARegion], "facets": Manager[Facet]}
)


def search_results(results: SearchResults, json_format: Optional[str] = None):
    return {
        "location": {
            "assembly": results["loc_search"]["assembly"],
            "chromosome": results["loc_search"]["location"].chromo,
            "start": results["loc_search"]["location"].range.lower,
            "end": results["loc_search"]["location"].range.upper,
        },
        "regions": dnaregions(results["dhss"], json_format),
        "facets": [
            {"name": f.name, "description": f.description, "values": [value.value for value in f.values.all()]}
            for f in results["facets"].all()
        ],
    }
