from enum import Enum
from typing import cast

from django.db.models import Q
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, DNAFeatureType, QueryToken
from cegs_portal.search.view_models.errors import ViewModelError
from cegs_portal.utils.http_exceptions import Http500


# TODO: create StrEnum class so e.g., `"ensemble" == IdType.ENSEMBL` works as expected
class IdType(Enum):
    ENSEMBL = "ensembl"
    NAME = "name"
    HAVANA = "havana"
    HGNC = "hgnc"
    ACCESSION = "accession"


class IdSearchType(Enum):
    EXACT = "exact"
    LIKE = "like"
    START = "start"
    IN = "in"


class LocSearchType(Enum):
    CLOSEST = "closest"
    EXACT = "exact"
    OVERLAP = "overlap"


def join_fields(*field_names):
    non_empty_fields = [field for field in field_names if field.strip() != ""]
    return "__".join(non_empty_fields)


class DNAFeatureSearch:
    @classmethod
    def id_search(cls, id_type, feature_id, search_type="exact", distinct=True):
        if id_type == IdType.ENSEMBL.value:
            field = "ensembl_id"
        elif id_type == IdType.HAVANA.value:
            field = "ids__havana"
        elif id_type == IdType.HGNC.value:
            field = "ids__hgnc"
        elif id_type == IdType.NAME.value:
            field = "name"
        elif id_type == IdType.ACCESSION.value:
            field = "accession_id"
        else:
            raise ViewModelError(f"Invalid ID type: {id_type}")

        if search_type == IdSearchType.EXACT.value:
            lookup = ""
        elif search_type == IdSearchType.LIKE.value:
            lookup = "icontains"
        elif search_type == IdSearchType.START.value:
            lookup = "istartswith"
        elif search_type == IdSearchType.IN.value:
            lookup = "in"
        else:
            raise ViewModelError(f"Invalid search type: {search_type}")

        field_lookup = join_fields(field, lookup)
        features = DNAFeature.objects.filter(**{field_lookup: feature_id}).prefetch_related(
            "children",
            "closest_gene",
            "closest_features",
            "source_for",
            "source_for__experiment",
            "source_for__facet_values",
            "source_for__facet_values__facet",
            "source_for__targets",
            "target_of",
            "target_of__experiment",
            "target_of__facet_values",
            "target_of__facet_values__facet",
            "target_of__sources",
        )
        if distinct:
            features = features.distinct()

        return features

    @classmethod
    def ids_search(
        cls,
        ids: list[tuple[QueryToken, str]],
        assembly: str,
        region_properties: list[str],
    ):

        query = {}

        if assembly is not None:
            query["ref_genome"] = assembly

        accession_ids = []
        ensembl_ids = []
        gene_names = []
        for id_type, feature_id in ids:
            if id_type == QueryToken.ACCESSION_ID:
                accession_ids.append(feature_id)
            elif id_type == QueryToken.ENSEMBL_ID:
                ensembl_ids.append(feature_id)
            elif id_type == QueryToken.GENE_NAME:
                gene_names.append(feature_id)
            else:
                raise Http500(f"Invalid Query Token: ({id_type}, {feature_id})")

        id_query = False
        if len(accession_ids) > 0:
            id_query = Q(accession_id__in=accession_ids)
        if len(ensembl_ids) > 0:
            if id_query:
                id_query |= Q(ensembl_id__in=ensembl_ids)
            else:
                id_query = Q(ensembl_id__in=ensembl_ids)
        if len(gene_names) > 0:
            if id_query:
                id_query |= Q(name__in=gene_names)
            else:
                id_query = Q(name__in=gene_names)

        prefetch_values = []

        if "regeffects" in region_properties:
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

        features = DNAFeature.objects.filter(id_query, **query).prefetch_related(*prefetch_values)

        return features

    @classmethod
    def loc_search(
        cls,
        chromo: str,
        start: str,
        end: str,
        assembly: str,
        feature_types: list[str],
        region_properties: list[str],
        search_type: str,
        facets: list[int] = cast(list[int], list),
    ):

        query = {"chrom_name": chromo}

        if len(feature_types) > 0:
            feature_type_db_values = [str(DNAFeatureType(f)) for f in feature_types]
            query["feature_type__in"] = feature_type_db_values

        field = "location"
        if search_type == LocSearchType.EXACT.value or search_type is None:
            lookup = ""
        elif search_type == LocSearchType.OVERLAP.value:
            lookup = "overlap"
        else:
            raise ViewModelError(f"Invalid search type: {search_type}")

        if assembly is not None:
            query["ref_genome"] = assembly

        field_lookup = join_fields(field, lookup)
        query[field_lookup] = NumericRange(int(start), int(end), "[)")

        prefetch_values = []
        if len(facets) > 0:
            prefetch_values = ["facet_values", "facet_values__facet"]

        if "regeffects" in region_properties:
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

        features = DNAFeature.objects.filter(**query).prefetch_related(*prefetch_values)

        if len(facets) > 0:
            features = features.filter(facet_values__in=facets)

        return features
