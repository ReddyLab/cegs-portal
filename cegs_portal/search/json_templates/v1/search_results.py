import re
from typing import Any, Optional, TypedDict

from django.db.models import Manager

from cegs_portal.search.json_templates.v1.dna_features import features
from cegs_portal.search.models import DNAFeature, Facet
from cegs_portal.search.models.utils import ChromosomeLocation
from cegs_portal.utils.pagination_types import Pageable

SearchResults = TypedDict(
    "SearchResults",
    {
        "location": ChromosomeLocation,
        "assembly": str,
        "features": Pageable[DNAFeature],
        "sig_reg_effects": dict[str : list[str]],
        "facets": Manager[Facet],
    },
)


def parse_source_locs_json(source_locs: str) -> list[str]:
    locs = []
    while match := re.search(r'\((chr\w+),\\"\[(\d+),(\d+)\)\\"\)', source_locs):
        chrom = match[1]
        start = int(match[2])
        end = int(match[3])
        locs.append((chrom, start, end))
        source_locs = source_locs[match.end() :]

    return locs


def parse_target_info_json(target_info: str) -> list[str]:
    info = []
    while match := re.search(r'\(chr\w+,\\"\[\d+,\d+\)\\",([\w-]+),(\w+)\)', target_info):
        gene_symbol = match[1]
        ensembl_id = match[2]
        info.append((gene_symbol, ensembl_id))
        target_info = target_info[match.end() :]
    return info


def parse_source_target_data_json(reo_data):
    return reo_data | {
        "source_locs": parse_source_locs_json(reo_data["source_locs"]),
        "target_info": parse_target_info_json(reo_data["target_info"]),
    }


def search_results(results: SearchResults, options: Optional[dict[str, Any]] = None):
    response: dict[str, Any] = {
        "features": features(results["features"], options),
        "sig_reg_effects": [
            (k, [parse_source_target_data_json(reo_data) for reo_data in reo_group])
            for k, reo_group in results["sig_reg_effects"]
        ],
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
