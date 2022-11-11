import re
from enum import Enum, auto
from typing import Optional, TypedDict
from urllib.parse import unquote_plus

from django.core.paginator import Paginator
from django.db.models.manager import BaseManager

from cegs_portal.search.forms import SearchForm
from cegs_portal.search.json_templates.v1.search_results import (
    search_results as sr_json,
)
from cegs_portal.search.models import ChromosomeLocation, Facet
from cegs_portal.search.models.dna_feature import DNAFeature
from cegs_portal.search.models.utils import QueryToken
from cegs_portal.search.view_models.v1 import Search
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.utils.http_exceptions import Http400

CHROMO_RE = re.compile(r"((chr\d?[123456789xym])\s*:\s*(\d+)(-(\d+))?)\s*", re.IGNORECASE)
ACCESSION_RE = re.compile(r"(DCP[a-z]{1,4}[0-9a-f]{8})\s*", re.IGNORECASE)
ENSEMBL_RE = re.compile(r"(ENS[0-9a-z]+)\s*", re.IGNORECASE)
ASSEMBLY_RE = re.compile(r"(hg19|hg38|grch37|grch38)\s*", re.IGNORECASE)
POSSIBLE_GENE_NAME_RE = re.compile(r"([A-Z0-9][A-Z0-9\.\-]+)\s*", re.IGNORECASE)


class ParseWarning(Enum):
    TOO_MANY_LOCS = auto()
    IGNORE_LOC = auto()
    IGNORE_TERMS = auto()


class SearchType(Enum):
    LOCATION = auto()
    ID = auto()


SearchResult = TypedDict(
    "SearchResult",
    {
        "location": Optional[ChromosomeLocation],
        "assembly": str,
        "features": BaseManager[DNAFeature],
        "facets": BaseManager[Facet],
        "search_type": str,
        "warnings": set[str],
    },
)


def parse_query(
    query: str,
) -> tuple[
    Optional[SearchType], list[tuple[QueryToken, str]], Optional[ChromosomeLocation], Optional[str], set[ParseWarning]
]:
    terms: list[tuple[QueryToken, str]] = []
    location: Optional[ChromosomeLocation] = None
    assembly: Optional[str] = None
    warnings: set[ParseWarning] = set()
    search_type = None

    query = query.replace(",", " ").strip()

    # Avoid an infinite loop by making sure `query` get shorter
    # every iteration and stopping if it doesn't
    old_query_len = len(query) + 1
    while query != "" and old_query_len != len(query):
        old_query_len = len(query)
        if match := re.match(CHROMO_RE, query):
            if search_type == SearchType.ID:
                warnings.add(ParseWarning.IGNORE_LOC)
            elif search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.TOO_MANY_LOCS)
            else:
                search_type = SearchType.LOCATION
                location = ChromosomeLocation(match.group(2), match.group(3), match.group(5))

            query = query[match.end() :]
            continue

        if match := re.match(ENSEMBL_RE, query):
            if search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.IGNORE_TERMS)
            else:
                terms.append(QueryToken.ENSEMBL_ID.associate(match.group(1)))
                search_type = SearchType.ID

            query = query[match.end() :]
            continue

        if match := re.match(ACCESSION_RE, query):
            if search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.IGNORE_TERMS)
            else:
                terms.append(QueryToken.ACCESSION_ID.associate(match.group(1)))
                search_type = SearchType.ID

            query = query[match.end() :]
            continue

        if match := re.match(ASSEMBLY_RE, query):
            token = match.group(1).lower()

            # Normalize token
            if token == "hg19" or token == "grch37":
                token = "GRCh37"
            elif token == "hg38" or token == "grch38":
                token = "GRCh38"
            assembly = token
            query = query[match.end() :]
            continue

        if match := re.match(POSSIBLE_GENE_NAME_RE, query):
            if search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.IGNORE_TERMS)
            else:
                terms.append(QueryToken.GENE_NAME.associate(match.group(1)))
                search_type = SearchType.ID

            query = query[match.end() :]
            continue

    return search_type, terms, location, assembly, warnings


class SearchView(TemplateJsonView):
    json_renderer = sr_json
    template = "search/v1/search_results.html"

    def request_options(self, request):
        options = super().request_options(request)
        options["search_query"] = request.GET.get("query", "")
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["feature_page"] = int(request.GET.get("feature_page", 1))
        return options

    def get(self, request, options, data):
        data["form"] = SearchForm()
        return super().get(request, options, data)

    def get_data(self, options):
        unquoted_search_query = unquote_plus(options["search_query"])
        search_type, query_terms, location, assembly_name, warnings = parse_query(unquoted_search_query)

        if search_type == SearchType.LOCATION:
            if location.range.lower >= location.range.upper:
                raise Http400(
                    f"Invalid location; lower bound ({location.range.lower}) "
                    f"larger than upper bound ({location.range.upper})"
                )
            if self.request.user.is_anonymous:
                features = Search.dnafeature_loc_search_public(location, assembly_name, options["facets"])
            elif self.request.user.is_superuser or self.request.user.is_portal_admin:
                features = Search.dnafeature_loc_search(location, assembly_name, options["facets"])
            else:
                features = Search.loc_search_with_private(
                    location, assembly_name, options["facets"], self.request.user.experiments
                )

            feature_paginator = Paginator(features, 20)
            features = feature_paginator.get_page(options["feature_page"])
        elif search_type == SearchType.ID:
            if self.request.user.is_anonymous:
                features = Search.dnafeature_id_search_public(query_terms, assembly_name)
            elif self.request.user.is_superuser or self.request.user.is_portal_admin:
                features = Search.dnafeature_id_search(query_terms, assembly_name)
            else:
                features = Search.dnafeature_id_search_with_private(
                    query_terms, assembly_name, self.request.user.experiments
                )

            if features.count() == 1:
                feature = features[0]
                width = feature.location.upper - feature.location.lower
                browser_padding = width // 10
                location = ChromosomeLocation(
                    # Increase the location "width" to ensure white space on either side of the feature in
                    # in the genome browser
                    feature.chrom_name,
                    str(max(0, feature.location.lower - browser_padding)),
                    str(feature.location.upper + browser_padding),
                )
                assembly_name = feature.ref_genome
        else:
            raise Http400(f"Invalid Query: {options['search_query']}")

        facets = Search.discrete_facet_search()

        return {
            "location": location,
            "assembly": assembly_name,
            "features": features,
            "facets": facets,
            "search_type": search_type.name,
            "query": options["search_query"],
            "facets_query": options["facets"],
            "warnings": {w.name for w in warnings},
        }
