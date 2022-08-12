from enum import Enum

from psycopg2.extras import NumericRange

from cegs_portal.search.models import FeatureAssembly
from cegs_portal.search.view_models.errors import ViewModelError


# TODO: create StrEnum class so e.g., `"ensemble" == IdType.ENSEMBL` works as expected
class IdType(Enum):
    ENSEMBL = "ensembl"
    NAME = "name"
    HAVANA = "havana"
    HGNC = "hgnc"


class LocSearchType(Enum):
    CLOSEST = "closest"
    EXACT = "exact"
    OVERLAP = "overlap"


def join_fields(*field_names):
    non_empty_fields = [field for field in field_names if field.strip() != ""]
    return "__".join(non_empty_fields)


class FeatureSearch:
    @classmethod
    def id_search(cls, id_type, feature_id):
        if id_type == IdType.ENSEMBL.value:
            field = "ensembl_id"
        elif id_type == IdType.HAVANA.value:
            field = "ids__havana"
        elif id_type == IdType.HGNC.value:
            field = "ids__hgnc"
        elif id_type == IdType.NAME.value:
            field = "name"
        else:
            raise ViewModelError(f"Invalid ID type: {id_type}")

        features = FeatureAssembly.objects.filter(**{field: feature_id}).prefetch_related(
            "children",
            "closest_features",
            "closest_features__regulatory_effects",
            "regulatory_effects",
            "regulatory_effects__sources",
            "regulatory_effects__facet_values",
        )

        return features.distinct()

    @classmethod
    def loc_search(cls, chromo, start, end, assembly, feature_types, search_type):
        query = {"chrom_name": chromo, "feature_type__in": feature_types}
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
        assemblies = FeatureAssembly.objects.filter(**query).select_related("parent").distinct()
        return assemblies
