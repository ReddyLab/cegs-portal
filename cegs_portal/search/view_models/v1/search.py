from typing import Optional

from django.db.models import Count, Q, Subquery

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
from cegs_portal.search.views.view_utils import UserType

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
        assembly: Optional[str] = None,
        private_experiments: Optional[list[str]] = None,
    ):
        return sig_reo_loc_search(
            (location.chromo, location.range.lower, location.range.upper), 5, private_experiments, assembly
        )

    @classmethod
    def categorical_facet_search(cls):
        return Facet.objects.filter(facet_type="FacetType.CATEGORICAL").prefetch_related("values").all()

    @classmethod
    def feature_counts(
        cls,
        region: ChromosomeLocation,
        assembly: str,
        user_type: UserType = UserType.ANONYMOUS,
        private_experiments: Optional[list[str]] = None,
    ):
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

        sig_reo_for_source_count = RegulatoryEffectObservation.objects.filter(sources__in=sources).exclude(
            facet_values__value=EffectObservationDirectionType.NON_SIGNIFICANT.value
        )

        sig_reo_for_gene_count = RegulatoryEffectObservation.objects.filter(targets__in=targets).exclude(
            facet_values__value=EffectObservationDirectionType.NON_SIGNIFICANT.value
        )

        match user_type:
            case UserType.ANONYMOUS:
                sig_reo_for_source_count = sig_reo_for_source_count.filter(Q(archived=False) & Q(public=True))
                sig_reo_for_gene_count = sig_reo_for_gene_count.filter(Q(archived=False) & Q(public=True))
            case UserType.LOGGED_IN:
                sig_reo_for_source_count = sig_reo_for_source_count.filter(
                    Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=private_experiments))
                )
                sig_reo_for_gene_count = sig_reo_for_gene_count.filter(
                    Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=private_experiments))
                )
            case UserType.ADMIN:
                pass  # Don't filter anything

        sig_reo_for_source_count = sig_reo_for_source_count.count()
        sig_reo_for_gene_count = sig_reo_for_gene_count.count()

        count_results = []
        count_results.append((EXPERIMENT_SOURCES_TEXT, count_dict[EXPERIMENT_SOURCES_TEXT], sig_reo_for_source_count))
        count_results.append((DNAFeatureType.GENE.value, count_dict[DNAFeatureType.GENE.value], sig_reo_for_gene_count))
        count_results.append((DNAFeatureType.TRANSCRIPT.value, count_dict[DNAFeatureType.TRANSCRIPT.value], 0))
        count_results.append((DNAFeatureType.EXON.value, count_dict[DNAFeatureType.EXON.value], 0))
        count_results.append((DNAFeatureType.CCRE.value, count_dict[DNAFeatureType.CCRE.value], 0))

        return count_results

    @classmethod
    def feature_sig_reos(
        cls,
        region: ChromosomeLocation,
        assembly: str,
        features: list[str],
        user_type: UserType = UserType.ANONYMOUS,
        private_experiments: Optional[list[str]] = None,
    ):
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
        )

        gene_features = DNAFeature.objects.filter(
            chrom_name=region.chromo,
            location__overlap=region.range,
            ref_genome=assembly,
        )

        # If no feature types are added, show all feature types. If at least one is added,
        # make sure to only show the added feature type(s).
        if len(sanitized_sources) > 0 or len(sanitized_genes) > 0:
            source_features = source_features.filter(feature_type__in=sanitized_sources)
            gene_features = gene_features.filter(feature_type__in=sanitized_genes)

        source_features = source_features.values("id")

        gene_features = gene_features.values("id")

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

        match user_type:
            case UserType.ANONYMOUS:
                source_sig_reos = source_sig_reos.filter(Q(archived=False) & Q(public=True))
                gene_sig_reos = gene_sig_reos.filter(Q(archived=False) & Q(public=True))
            case UserType.LOGGED_IN:
                source_sig_reos = source_sig_reos.filter(
                    Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=private_experiments))
                )
                gene_sig_reos = gene_sig_reos.filter(
                    Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=private_experiments))
                )
            case UserType.ADMIN:
                pass  # Do no filtering

        return sorted(source_sig_reos.union(gene_sig_reos).all(), key=lambda x: x.significance)
