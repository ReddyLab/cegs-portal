from typing import Optional

from cegs_portal.search.models import ChromosomeLocation, Facet
from cegs_portal.search.models.utils import IdType
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, LocSearchType


class Search:
    @classmethod
    def dnafeature_ids_search(cls, ids: list[tuple[IdType, str]], assembly: Optional[str]):
        return DNAFeatureSearch.ids_search(
            ids,
            assembly,
            [],
        )

    @classmethod
    def dnafeature_ids_search_public(cls, ids: list[tuple[IdType, str]], assembly: Optional[str]):
        return DNAFeatureSearch.ids_search_public(
            ids,
            assembly,
            [],
        )

    @classmethod
    def dnafeature_ids_search_with_private(
        cls, ids: list[tuple[IdType, str]], assembly: Optional[str], private_experiments: list[str]
    ):
        return DNAFeatureSearch.ids_search_with_private(
            ids,
            assembly,
            [],
            private_experiments,
        )

    @classmethod
    def dnafeature_loc_search(cls, location: ChromosomeLocation, assembly: Optional[str], facets: list[int]):
        return DNAFeatureSearch.loc_search(
            location.chromo,
            str(location.range.lower),
            str(location.range.upper),
            assembly,
            [DNAFeatureSearch.SEARCH_RESULTS_PFT],
            [],
            LocSearchType.OVERLAP.value,
            facets,
        )

    @classmethod
    def dnafeature_loc_search_public(cls, location: ChromosomeLocation, assembly: Optional[str], facets: list[int]):
        return DNAFeatureSearch.loc_search_public(
            location.chromo,
            str(location.range.lower),
            str(location.range.upper),
            assembly,
            [DNAFeatureSearch.SEARCH_RESULTS_PFT],
            [],
            LocSearchType.OVERLAP.value,
            facets,
        )

    @classmethod
    def dnafeature_loc_search_with_private(
        cls, location: ChromosomeLocation, assembly: Optional[str], facets: list[int], private_experiments: list[str]
    ):
        return DNAFeatureSearch.loc_search_with_private(
            location.chromo,
            str(location.range.lower),
            str(location.range.upper),
            assembly,
            [DNAFeatureSearch.SEARCH_RESULTS_PFT],
            [],
            LocSearchType.OVERLAP.value,
            facets,
            private_experiments,
        )

    @classmethod
    def discrete_facet_search(cls):
        return Facet.objects.filter(facet_type="FacetType.DISCRETE").prefetch_related("values").all()
