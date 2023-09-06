from typing import Optional

from django.db.models import Count

from cegs_portal.get_expr_data.view_models import sig_reo_loc_search
from cegs_portal.search.models import (
    ChromosomeLocation,
    DNAFeature,
    DNAFeatureType,
    Facet,
)
from cegs_portal.search.models.utils import IdType
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, LocSearchType

EXPERIMENT_SOURCES = "Experiment Regulatory Effect Source"


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
        cls, location: ChromosomeLocation, assembly: str, facets: list[int], private_experiments: list[str]
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
    def sig_reo_loc_search(
        cls,
        location: ChromosomeLocation,
        private_experiments: Optional[list[str]] = None,
        assembly: Optional[str] = None,
    ):
        return sig_reo_loc_search(
            (location.chromo, location.range.lower, location.range.upper), 5, private_experiments, assembly
        )

    @classmethod
    def categorical_facet_search(cls):
        return Facet.objects.filter(facet_type="FacetType.CATEGORICAL").prefetch_related("values").all()

    @classmethod
    def feature_counts(cls, region: ChromosomeLocation, assembly: str):
        counts = (
            DNAFeature.objects.filter(chrom_name=region.chromo, location__overlap=region.range, ref_genome=assembly)
            .values("feature_type")
            .annotate(count=Count("accession_id"))
        )

        count_dict = {
            DNAFeatureType.CCRE.value: 0,
            DNAFeatureType.EXON.value: 0,
            DNAFeatureType.GENE.value: 0,
            EXPERIMENT_SOURCES: 0,
            DNAFeatureType.TRANSCRIPT.value: 0,
        }
        for count in counts:
            count_value = DNAFeatureType.from_db_str(count["feature_type"]).value
            if count_value in count_dict:
                count_dict[count_value] += count["count"]
            else:
                count_dict[EXPERIMENT_SOURCES] += count["count"]

        return sorted([(name + "s", count) for name, count in count_dict.items()], key=lambda x: x[0])
