from typing import Optional

from django.db.models import Count, Subquery

from cegs_portal.get_expr_data.view_models import sig_reo_loc_search
from cegs_portal.search.models import (
    ChromosomeLocation,
    DNAFeature,
    DNAFeatureType,
    EffectObservationDirectionType,
    Facet,
    RegulatoryEffectObservation,
)
from cegs_portal.search.models.utils import IdType
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, LocSearchType

EXPERIMENT_SOURCES = [DNAFeatureType.CAR.value, DNAFeatureType.GRNA.value, DNAFeatureType.DHS.value]
EXPERIMENT_SOURCES_TEXT = "Experiment Regulatory Effect Source"


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
            .values("feature_type", "id")
            .annotate(count=Count("accession_id"))
        )

        count_dict = {
            DNAFeatureType.CCRE.value: 0,
            DNAFeatureType.EXON.value: 0,
            DNAFeatureType.GENE.value: 0,
            EXPERIMENT_SOURCES_TEXT: 0,
            DNAFeatureType.TRANSCRIPT.value: 0,
        }
        sources = []
        targets = []
        for count in counts:
            count_value = DNAFeatureType.from_db_str(count["feature_type"]).value
            if count_value in count_dict:
                count_dict[count_value] += count["count"]
            elif count_value in EXPERIMENT_SOURCES:
                count_dict[EXPERIMENT_SOURCES_TEXT] += count["count"]
            else:
                raise ValueError(f'Unknown DNA Feature Type "{count_value}"')

            match count["feature_type"]:
                case "DNAFeatureType.CAR" | "DNAFeatureType.GRNA" | "DNAFeatureType.DHS":
                    sources.append(count["id"])
                case "DNAFeatureType.GENE":
                    targets.append(count["id"])

        sig_reo_for_gene_count = (
            RegulatoryEffectObservation.objects.filter(targets__in=targets)
            .exclude(facet_values__value=EffectObservationDirectionType.NON_SIGNIFICANT.value)
            .count()
        )

        sig_reo_for_source_count = (
            RegulatoryEffectObservation.objects.filter(sources__in=sources)
            .exclude(facet_values__value=EffectObservationDirectionType.NON_SIGNIFICANT.value)
            .count()
        )

        count_results = []
        count_results.append((EXPERIMENT_SOURCES_TEXT, count_dict[EXPERIMENT_SOURCES_TEXT], sig_reo_for_source_count))
        count_results.append((DNAFeatureType.GENE.value, count_dict[DNAFeatureType.GENE.value], sig_reo_for_gene_count))
        count_results.append((DNAFeatureType.TRANSCRIPT.value, count_dict[DNAFeatureType.TRANSCRIPT.value], 0))
        count_results.append((DNAFeatureType.EXON.value, count_dict[DNAFeatureType.EXON.value], 0))
        count_results.append((DNAFeatureType.CCRE.value, count_dict[DNAFeatureType.CCRE.value], 0))

        return count_results

    @classmethod
    def feature_sig_reos(cls, region: ChromosomeLocation, assembly: str, features: list[str]):
        sanitized_sources = []
        sanitized_genes = []
        for feature in features:
            match feature.lower():
                case "car":
                    sanitized_sources.append(DNAFeatureType.CAR)
                case "grna":
                    sanitized_sources.append(DNAFeatureType.GRNA)
                case "dhs":
                    sanitized_sources.append(DNAFeatureType.DHS)
                case "gene":
                    sanitized_genes.append(DNAFeatureType.GENE)

        source_features = DNAFeature.objects.filter(
            chrom_name=region.chromo,
            location__overlap=region.range,
            ref_genome=assembly,
            feature_type__in=sanitized_sources,
        ).values("id")

        gene_features = DNAFeature.objects.filter(
            chrom_name=region.chromo,
            location__overlap=region.range,
            ref_genome=assembly,
            feature_type__in=sanitized_genes,
        ).values("id")

        source_sig_reos = (
            RegulatoryEffectObservation.objects.filter(sources__in=Subquery(source_features))
            .exclude(facet_values__value=EffectObservationDirectionType.NON_SIGNIFICANT.value)
            .select_related("experiment")
            .prefetch_related("sources", "targets")
        )

        gene_sig_reos = (
            RegulatoryEffectObservation.objects.filter(targets__in=Subquery(gene_features))
            .exclude(facet_values__value=EffectObservationDirectionType.NON_SIGNIFICANT.value)
            .select_related("experiment")
            .prefetch_related("sources", "targets")
        )

        return sorted(source_sig_reos.union(gene_sig_reos).all(), key=lambda x: x.significance)
