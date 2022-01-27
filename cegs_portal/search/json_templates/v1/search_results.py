from typing import Any

from cegs_portal.search.json_templates.v1.dna_region import dnaregions


def search_results(results: dict[str, Any], json_format: bool = None):
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
