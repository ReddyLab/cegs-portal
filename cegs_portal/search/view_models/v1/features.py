from enum import Enum

from psycopg2.extras import NumericRange

from cegs_portal.search.models import Feature, FeatureAssembly
from cegs_portal.search.view_models.errors import ViewModelError


# TODO: create StrEnum class so e.g., `"ensemble" == IdType.ENSEMBL` works as expected
class IdType(Enum):
    ENSEMBL = "ensembl"
    NAME = "name"
    HAVANA = "havana"
    HGNC = "hgnc"
    DB = "db"


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


class FeatureSearch:
    @classmethod
    def id_search(cls, id_type, feature_id, search_type="exact", distinct=True):
        if id_type == IdType.ENSEMBL.value:
            field = "ensembl_id"
        elif id_type == IdType.HAVANA.value:
            field = "assemblies__ids__havana"
        elif id_type == IdType.HGNC.value:
            field = "assemblies__ids__hgnc"
        elif id_type == IdType.NAME.value:
            field = "assemblies__name"
        elif id_type == IdType.DB.value:
            field = "id"
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
        features = Feature.objects.filter(**{field_lookup: feature_id}).prefetch_related(
            "assemblies",
            "children",
            "children__assemblies",
            "dnaregion_set",
            "dnaregion_set__regulatory_effects",
            "regulatory_effects",
            "regulatory_effects__sources",
        )
        if distinct:
            features = features.distinct()

        return features

    @classmethod
    def loc_search(cls, chromo, start, end, assembly, feature_types, search_type):
        query = {"chrom_name": chromo, "feature__feature_type__in": feature_types}
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
        query[field_lookup] = NumericRange(int(start), int(end), "[]")
        assemblies = FeatureAssembly.objects.filter(**query).select_related("feature", "feature__parent").distinct()
        return assemblies
