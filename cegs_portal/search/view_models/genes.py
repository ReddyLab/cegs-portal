from enum import Enum
from typing import Optional

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


class GeneSearch:
    @classmethod
    def id_search(cls, id_type, gene_id, search_type="exact", distinct=True):
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
        genes = Feature.objects.filter(**{"feature_type": "gene", field_lookup: gene_id})

        if distinct:
            genes = genes.distinct()
        return genes

    @classmethod
    def loc_search(cls, chromo, start, end, assembly, search_type):
        if search_type == LocSearchType.CLOSEST.value:
            return cls._closest_loc_search(chromo, start, end, assembly)

        return cls._std_loc_search(chromo, start, end, assembly, search_type)

    @classmethod
    def _std_loc_search(cls, chromo, start, end, assembly, search_type):
        query = {"feature_type": "gene", "assemblies__chrom_name": chromo}
        field = "assemblies__location"
        if search_type == LocSearchType.EXACT.value or search_type is None:
            lookup = ""
        elif search_type == LocSearchType.OVERLAP.value:
            lookup = "overlap"
        else:
            raise ViewModelError(f"Invalid search type: {search_type}")

        if assembly is not None:
            query["assemblies__ref_genome"] = assembly

        field_lookup = join_fields(field, lookup)
        query[field_lookup] = NumericRange(int(start), int(end), "[]")
        genes = Feature.objects.filter(**query).distinct()
        return genes

    @classmethod
    def _closest_loc_search(cls, chromo, start, end, assembly) -> Optional[Feature]:
        query_lt = {"feature__feature_type": "gene", "chrom_name": chromo}
        query_gt = {"feature__feature_type": "gene", "chrom_name": chromo}

        if assembly is not None:
            query_lt["ref_genome"] = assembly
            query_gt["ref_genome"] = assembly

        field = "location"
        lt_field_lookup = join_fields(field, "lt")
        gt_field_lookup = join_fields(field, "gt")
        query_lt[lt_field_lookup] = NumericRange(int(start), int(end), "[]")
        query_gt[gt_field_lookup] = NumericRange(int(start), int(end), "[]")
        lower_gene = FeatureAssembly.objects.filter(**query_lt).order_by("-location").select_related("feature").first()
        higher_gene = FeatureAssembly.objects.filter(**query_gt).order_by("location").select_related("feature").first()

        if lower_gene is None and higher_gene is None:
            return None

        if lower_gene is None:
            assert higher_gene is not None
            return higher_gene.feature

        if higher_gene is None:
            assert lower_gene is not None
            return lower_gene.feature

        lower_dist = start - lower_gene.location.lower
        higher_dist = higher_gene.location.lower - start
        if lower_dist > higher_dist:
            return higher_gene.feature

        return lower_gene.feature
