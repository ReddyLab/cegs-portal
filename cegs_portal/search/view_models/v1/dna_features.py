from enum import Enum, StrEnum
from typing import Any, Optional, cast

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, OuterRef, Q, QuerySet, Subquery
from psycopg.types.range import Int4Range

from cegs_portal.search.models import (
    DNAFeature,
    DNAFeatureType,
    Facet,
    FacetValue,
    IdType,
    RegulatoryEffectObservation,
    RegulatoryEffectObservationSet,
)
from cegs_portal.search.view_models.errors import ObjectNotFoundError, ViewModelError
from cegs_portal.search.view_models.v1.non_targeting_reos import (
    DNAFeatureNonTargetSearch,
)
from cegs_portal.utils.http_exceptions import Http500


class LocSearchType(Enum):
    CLOSEST = "closest"
    EXACT = "exact"
    OVERLAP = "overlap"


class LocSearchProperty(StrEnum):
    EFFECT_DIRECTIONS = "effect_directions"
    PARENT_INFO = "parent_info"
    REG_EFFECTS = "regeffects"
    REO_SOURCE = "reo_source"
    SCREEN_CCRE = "screen_ccre"
    SIGNIFICANT = "significant"
    REPORTER_ASSAY = "reporterassay"
    CRISPRI = "crispri"
    CRISPRA = "crispra"


REO_COUNT_PROPERTIES = {
    LocSearchProperty.EFFECT_DIRECTIONS,
    LocSearchProperty.SIGNIFICANT,
    LocSearchProperty.REO_SOURCE,
}

FUNCTIONAL_CHARACTERIZATION_PROPERTIES = {
    LocSearchProperty.REPORTER_ASSAY,
    LocSearchProperty.CRISPRI,
    LocSearchProperty.CRISPRA,
}

FUNCTIONAL_CHARACTERIZATION_VALUES = {
    LocSearchProperty.REPORTER_ASSAY.value: "Reporter Assay",
    LocSearchProperty.CRISPRI.value: "CRISPRi",
    LocSearchProperty.CRISPRA.value: "CRISPRa",
}


def join_fields(*field_names):
    non_empty_fields = [field for field in field_names if field.strip() != ""]
    return "__".join(non_empty_fields)


class DNAFeatureSearch:
    SEARCH_RESULTS_PFT = "search_results"
    PSEUDO_FEATURE_TYPES = {
        SEARCH_RESULTS_PFT: set(DNAFeatureType) - set([DNAFeatureType.EXON, DNAFeatureType.TRANSCRIPT])
    }

    @classmethod
    def id_search(
        cls,
        id_type: str,
        feature_id: str,
        assembly: Optional[str] = None,
        feature_properties: Optional[list[str]] = None,
        distinct=True,
    ) -> QuerySet[DNAFeature]:
        query = {}

        if feature_properties is None:
            feature_properties = []

        if id_type == IdType.ENSEMBL:
            query["ensembl_id"] = feature_id
        elif id_type == IdType.GENE_NAME:
            query["name__iexact"] = feature_id
        elif id_type == IdType.ACCESSION:
            query["accession_id"] = feature_id
        else:
            raise ViewModelError(f"Invalid ID type: {id_type}")

        if assembly is not None:
            query["ref_genome"] = assembly

        features = DNAFeature.objects.filter(**query).prefetch_related(
            "children",
            "closest_features",
        )

        if "regeffects" in feature_properties:
            features = features.prefetch_related("source_for", "target_of")

        if distinct:
            features = features.distinct()

        return features

    @classmethod
    def expr_id(cls, feature_id: str) -> str:
        if feature_id.startswith("DCP"):
            feature = DNAFeature.objects.filter(accession_id=feature_id).values_list(
                "experiment_accession_id", flat=True
            )
        elif feature_id.startswith("ENS"):
            feature = DNAFeature.objects.filter(ensembl_id=feature_id).values_list("experiment_accession_id", flat=True)
        else:
            feature = DNAFeature.objects.filter(name__iexact=feature_id).values_list(
                "experiment_accession_id", flat=True
            )

        if len(feature) == 0:
            raise ObjectNotFoundError(f"DNA Feature {feature_id} not found")

        return cast(str, feature[0])

    @classmethod
    def is_public(cls, feature_id: str) -> bool:
        if feature_id.startswith("DCP"):
            feature = DNAFeature.objects.filter(accession_id=feature_id).values_list("public", flat=True)
        elif feature_id.startswith("ENS"):
            feature = DNAFeature.objects.filter(ensembl_id=feature_id).values_list("public", flat=True)
        else:
            feature = DNAFeature.objects.filter(name__iexact=feature_id).values_list("public", flat=True)

        if len(feature) == 0:
            raise ObjectNotFoundError(f"DNA Feature {feature_id} not found")

        return cast(bool, feature[0])

    @classmethod
    def is_archived(cls, feature_id: str) -> bool:
        if feature_id.startswith("DCP"):
            feature = DNAFeature.objects.filter(accession_id=feature_id).values_list("archived", flat=True)
        elif feature_id.startswith("ENS"):
            feature = DNAFeature.objects.filter(ensembl_id=feature_id).values_list("archived", flat=True)
        else:
            feature = DNAFeature.objects.filter(name__iexact=feature_id).values_list("archived", flat=True)

        if len(feature) == 0:
            raise ObjectNotFoundError(f"DNA Feature {feature_id} not found")

        return cast(bool, feature[0])

    @classmethod
    def ids_search(
        cls,
        ids: list[tuple[IdType, str]],
        assembly: Optional[str],
        feature_properties: list[str],
    ) -> QuerySet[DNAFeature]:
        query = {}

        if assembly is not None:
            query["ref_genome"] = assembly

        accession_ids = []
        ensembl_ids = []
        gene_names = []
        for id_type, feature_id in ids:
            if id_type == IdType.ACCESSION:
                accession_ids.append(feature_id)
            elif id_type == IdType.ENSEMBL:
                ensembl_ids.append(feature_id)
            elif id_type == IdType.GENE_NAME:
                gene_names.append(feature_id)
            else:
                raise Http500(f"Invalid Query Token: ({id_type}, {feature_id})")

        id_query = None
        if len(accession_ids) > 0:
            id_query = Q(accession_id__in=accession_ids)
        if len(ensembl_ids) > 0:
            if id_query is not None:
                id_query |= Q(ensembl_id__in=ensembl_ids)
            else:
                id_query = Q(ensembl_id__in=ensembl_ids)
        if len(gene_names) > 0:
            if id_query is not None:
                id_query |= Q(name__in=gene_names)
            else:
                id_query = Q(name__in=gene_names)

        prefetch_values = []

        if "regeffects" in feature_properties:
            prefetch_values.extend(
                [
                    "source_for",
                    "source_for__facet_values",
                    "source_for__facet_values__facet",
                    "source_for__targets",
                    "target_of",
                    "target_of__facet_values",
                    "target_of__facet_values__facet",
                ]
            )

        features = DNAFeature.objects.filter(id_query, **query).prefetch_related(*prefetch_values).distinct()

        return features

    @classmethod
    def ids_search_public(cls, *args, **kwargs):
        return cls.ids_search(*args, *kwargs).filter(public=True, archived=False)

    @classmethod
    def ids_search_with_private(cls, *args, **kwargs):
        return cls.ids_search(*args[:-1], *kwargs).filter(
            Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=args[-1]))
        )

    @classmethod
    def loc_search(
        cls,
        chromo: str,
        start: str,
        end: str,
        assembly: Optional[str],
        feature_types: list[str],
        feature_properties: list[str],
        search_type: str,
        facets: list[int] = cast(list[int], list),
    ) -> QuerySet[DNAFeature]:
        filters: dict[str, Any] = {"chrom_name": chromo}
        feature_properties_set = set(feature_properties)

        new_feature_types: list[DNAFeatureType] = []
        for ft in feature_types:
            if ft in cls.PSEUDO_FEATURE_TYPES:
                new_feature_types.extend(cls.PSEUDO_FEATURE_TYPES[ft])
            else:
                new_feature_types.append(DNAFeatureType(ft))

        if len(new_feature_types) > 0:
            filters["feature_type__in"] = new_feature_types

        field = "location"
        if search_type == LocSearchType.EXACT.value:
            lookup = ""
        elif search_type == LocSearchType.OVERLAP.value or search_type is None:
            lookup = "overlap"
        else:
            raise ViewModelError(f"Invalid search type: {search_type}")

        if assembly is not None:
            filters["ref_genome"] = assembly

        field_lookup = join_fields(field, lookup)
        filters[field_lookup] = Int4Range(int(start), int(end), "[)")

        prefetch_values = ["parent", "parent_accession"]

        if LocSearchProperty.SCREEN_CCRE in feature_properties:
            ccre_facet_id = Facet.objects.get(name="cCRE Category").id
            ccre_facet_values = FacetValue.objects.filter(facet_id=ccre_facet_id).values_list("id", flat=True)
            facets += ccre_facet_values

        if len(facets) > 0:
            filters["facet_values__id__in"] = facets
            prefetch_values.extend(["facet_values", "facet_values__facet"])

        included_fcp = feature_properties_set & FUNCTIONAL_CHARACTERIZATION_PROPERTIES

        if LocSearchProperty.REG_EFFECTS in feature_properties or len(included_fcp) > 0:
            # The facet presets are used when getting the "direction" property
            # of a RegulatoryEffectObservation. This is done in the _reg_effect.html partial
            # and the reg_effect function of the dna_features.py json template.
            prefetch_values.extend(
                [
                    "source_for",
                    "source_for__facet_values",
                    "source_for__facet_values__facet",
                    "source_for__sources",
                    "source_for__targets",
                    "target_of",
                    "target_of__facet_values",
                    "target_of__facet_values__facet",
                    "target_of__sources",
                    "target_of__targets",
                ]
            )

        features = DNAFeature.objects

        if any(p in REO_COUNT_PROPERTIES for p in feature_properties):
            # skip any feature that are not the sources for any REOs
            features = features.annotate(reo_count=Count("source_for"))
            filters["reo_count__gt"] = 0

        if len(included_fcp) > 0:
            # we want to filter on functional characterization modality type

            # Convert from e.g., "reporterassay" (the property value) to
            # e.g., "Reporter Assay", the value in the DB.
            db_fcp = [FUNCTIONAL_CHARACTERIZATION_VALUES[p] for p in included_fcp]

            # count how many times one of the requested functional characterization values
            # shows up in REOs this feature is a source for
            features = features.annotate(
                source_fcp=Count(
                    "source_for__facet_values__value",
                    filter=Q(source_for__facet_values__value__in=db_fcp),
                )
            )

            # count how many times one of the requested functional characterization values
            # shows up in REOs this feature is a target of
            features = features.annotate(
                target_fcp=Count(
                    "target_of__facet_values__value",
                    filter=Q(source_for__facet_values__value__in=db_fcp),
                )
            )

            # Only include this feature is it's a source for or target of at least one
            # reo with a requested functional characterization type
            features = features.filter(Q(source_fcp__gt=0) | Q(target_fcp__gt=0))

        if LocSearchProperty.EFFECT_DIRECTIONS in feature_properties:
            features = features.annotate(
                effect_directions=ArrayAgg(
                    "source_for__facet_values__value",
                    filter=Q(source_for__facet_values__facet__name="Direction"),
                    default=[],
                )
            )

        if LocSearchProperty.SIGNIFICANT in feature_properties:
            features = features.annotate(
                sig_count=Count(
                    "source_for__facet_values__value",
                    filter=Q(source_for__facet_values__value__in=["Depleted Only", "Enriched Only", "Mixed"]),
                )
            )
            filters["sig_count__gt"] = 0

        if LocSearchProperty.SCREEN_CCRE in feature_properties:
            features = features.annotate(
                ccre_type=Subquery(FacetValue.objects.filter(id__in=OuterRef("facet_values__id")).values("value"))
            )

        features = features.filter(**filters).prefetch_related(*prefetch_values).select_related("parent")

        return features.order_by("location")

    @classmethod
    def loc_search_public(cls, *args, **kwargs):
        return cls.loc_search(*args, *kwargs).filter(public=True, archived=False)

    @classmethod
    def loc_search_with_private(cls, *args, **kwargs):
        return cls.loc_search(*args[:-1], *kwargs).filter(
            Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=args[-1]))
        )

    @classmethod
    def source_reo_search(cls, source_id: str):
        reg_effects = (
            cast(RegulatoryEffectObservationSet, RegulatoryEffectObservation.objects)
            .with_facet_values()
            .filter(sources__accession_id=source_id)
            .exclude(facet_values__value="Non-significant")
        )

        return reg_effects

    @classmethod
    def target_reo_search(cls, source_id: str):
        reg_effects = (
            cast(RegulatoryEffectObservationSet, RegulatoryEffectObservation.objects)
            .with_facet_values()
            .filter(targets__accession_id=source_id)
            .exclude(facet_values__value="Non-significant")
        )

        return reg_effects

    @classmethod
    def non_targeting_reo_search(cls, feature_accession_id: str, sig_only: bool):
        return DNAFeatureNonTargetSearch.non_targeting_regeffect_search(feature_accession_id, sig_only)
