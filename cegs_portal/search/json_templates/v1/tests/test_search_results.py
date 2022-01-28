import pytest
from django.db.models import Manager

from cegs_portal.search.json_templates.v1.dna_region import dnaregions
from cegs_portal.search.json_templates.v1.search_results import SearchResults
from cegs_portal.search.json_templates.v1.search_results import (
    search_results as sr_json,
)
from cegs_portal.search.models import DNARegion, Facet
from cegs_portal.search.models.utils import ChromosomeLocation
from cegs_portal.utils.pagination_types import Pageable

pytestmark = pytest.mark.django_db


def test_search_results(regions: Pageable[DNARegion], facets: Manager[Facet]):
    search_results: SearchResults = {
        "loc_search": {
            "location": ChromosomeLocation("chr1", "10000", "15000"),
            "assembly": "GRCh37",
        },
        "dhss": regions,
        "facets": facets,
    }

    assert sr_json(search_results) == {
        "location": {
            "assembly": search_results["loc_search"]["assembly"],
            "chromosome": search_results["loc_search"]["location"].chromo,
            "start": search_results["loc_search"]["location"].range.lower,
            "end": search_results["loc_search"]["location"].range.upper,
        },
        "regions": dnaregions(search_results["dhss"]),
        "facets": [
            {"name": f.name, "description": f.description, "values": [value.value for value in f.values.all()]}
            for f in search_results["facets"].all()
        ],
    }

    assert sr_json(search_results, json_format="genoverse") == {
        "location": {
            "assembly": search_results["loc_search"]["assembly"],
            "chromosome": search_results["loc_search"]["location"].chromo,
            "start": search_results["loc_search"]["location"].range.lower,
            "end": search_results["loc_search"]["location"].range.upper,
        },
        "regions": dnaregions(search_results["dhss"], json_format="genoverse"),
        "facets": [
            {"name": f.name, "description": f.description, "values": [value.value for value in f.values.all()]}
            for f in search_results["facets"].all()
        ],
    }
