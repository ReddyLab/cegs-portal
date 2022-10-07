import re
from enum import Enum, auto
from typing import Optional, TypedDict

from django.db.models.manager import BaseManager

from cegs_portal.search.models import ChromosomeLocation, Facet
from cegs_portal.search.models.dna_feature import DNAFeature
from cegs_portal.search.models.utils import QueryToken
from cegs_portal.search.view_models.errors import ViewModelError
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, LocSearchType
from cegs_portal.utils.http_exceptions import Http400

CHROMO_RE = re.compile(r"((chr[12]?[123456789xym])\s*:\s*(\d+)(-(\d+))?)\s*", re.IGNORECASE)
ACCESSION_RE = re.compile(r"(DCP[a-z]{1,4}[0-9a-f]{8})\s*", re.IGNORECASE)
ENSEMBL_RE = re.compile(r"(ENS[0-9a-z]+)\s*", re.IGNORECASE)
# HAVANA_RE = re.compile(r"\s*(OTT[0-9a-z]+)", re.IGNORECASE)
# HUGO_RE = re.compile(r"\s*(HGNC:[0-9a-z]+)", re.IGNORECASE)
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
        "warnings": set[ParseWarning],
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

    while query != "":
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


class Search:
    @classmethod
    def _dnafeature_id_search(cls, ids: list[tuple[QueryToken, str]], assembly: str):
        regions = DNAFeatureSearch.ids_search(
            ids,
            assembly,
            [],
        )

        return regions

    @classmethod
    def _dnafeature_loc_search(cls, location: ChromosomeLocation, assembly: str, facets: list[int]):
        if location.range.lower >= location.range.upper:
            raise ViewModelError(
                f"Invalid location; lower bound ({location.range.lower}) "
                f"larger than upper bound ({location.range.upper})"
            )

        regions = DNAFeatureSearch.loc_search(
            location.chromo,
            str(location.range.lower),
            str(location.range.upper),
            assembly,
            [],
            [],
            LocSearchType.OVERLAP.value,
            facets,
        )

        return regions

    @classmethod
    def search(cls, query_string: str, facets: list[int] = list) -> SearchResult:
        search_type, query_terms, location, assembly_name, warnings = parse_query(query_string)
        facet_results = Facet.objects.filter(facet_type="FacetType.DISCRETE").prefetch_related("values").all()

        if search_type == SearchType.LOCATION:
            features = cls._dnafeature_loc_search(location, assembly_name, facets)
        elif search_type == SearchType.ID:
            features = cls._dnafeature_id_search(query_terms, assembly_name)
        else:
            raise Http400(f"Invalid Query: {query_string}")

        return {
            "location": location,
            "assembly": assembly_name,
            "features": features,
            "facets": facet_results,
            "warnings": {w.name for w in warnings},
        }
