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
        "sig_reg_effects": dict[str, list[str]],
        "facets": Manager[Facet],
    },
)


def parse_source_locs_json(source_locs: list[tuple[Optional[str], Optional[str], Optional[str]]]) -> list[str]:
    locs = []
    for source_loc in source_locs:
        if source_loc[0] is None:
            continue

        chrom, loc, accession_id = source_loc
        if match := re.match(r"\[(\d+),(\d+)\)", loc):
            start = int(match[1])
            end = int(match[2])
            locs.append((chrom, start, end, accession_id))

    return locs


def parse_target_info_json(
    target_infos: list[tuple[Optional[str], Optional[str], Optional[str], Optional[str]]]
) -> list[str]:
    info = []
    for target_info in target_infos:
        if target_info[2] is None:
            continue

        _, _, gene_symbol, ensembl_id = target_info
        info.append((gene_symbol, ensembl_id))
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
