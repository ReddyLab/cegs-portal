from enum import Enum

from psycopg2.extras import NumericRange

from cegs_portal.search.models import Gene, GeneAssembly
from cegs_portal.search.view_models.errors import ViewModelError


# TODO: create StrEnum class so e.g., `"ensemble" == IdType.ENSEMBL` works as expected
class IdType(Enum):
    ENSEMBL = "ensembl"
    NAME = "name"
    HAVANA = "havana"
    HGNC = "hgnc"


class IdSearchType(Enum):
    EXACT = "exact"
    LIKE = "like"
    START = "start"


class LocSearchType(Enum):
    CLOSEST = "closest"
    EXACT = "exact"
    OVERLAP = "overlap"


def join_fields(*field_names):
    non_empty_fields = [field for field in field_names if field.strip() != ""]
    return "__".join(non_empty_fields)


class GeneSearch:
    @classmethod
    def id_search(cls, id_type, gene_id, search_type="exact"):
        if id_type == IdType.ENSEMBL.value:
            field = "ensembl_id"
        elif id_type == IdType.HAVANA.value:
            field = "assemblies__ids__havana"
        elif id_type == IdType.HGNC.value:
            field = "assemblies__ids__hgnc"
        elif id_type == IdType.NAME.value:
            field = "assemblies__name"
        else:
            raise ViewModelError(f"Invalid ID type: {id_type}")

        if search_type == IdSearchType.EXACT.value:
            lookup = ""
        elif search_type == IdSearchType.LIKE.value:
            lookup = "icontains"
        elif search_type == IdSearchType.START.value:
            lookup = "istartswith"
        else:
            raise ViewModelError(f"Invalid search type: {search_type}")

        field_lookup = join_fields(field, lookup)
        genes = Gene.objects.filter(**{field_lookup: gene_id}).distinct()
        return genes

    @classmethod
    def loc_search(cls, chromo, start, end, assembly, search_type):
        if search_type == LocSearchType.CLOSEST.value:
            return cls._closest_loc_search(chromo, start, end, assembly)

        return cls._std_loc_search(chromo, start, end, assembly, search_type)

    @classmethod
    def _std_loc_search(cls, chromo, start, end, assembly, search_type):
        query = {"assemblies__chrom_name": chromo}
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
        genes = Gene.objects.filter(**query).distinct()
        return genes

    @classmethod
    def _closest_loc_search(cls, chromo, start, end, assembly):
        query_lt = {"chrom_name": chromo}
        query_gt = {"chrom_name": chromo}

        if assembly is not None:
            query_lt["ref_genome"] = assembly
            query_gt["ref_genome"] = assembly

        field = "location"
        lt_field_lookup = join_fields(field, "lt")
        gt_field_lookup = join_fields(field, "gt")
        query_lt[lt_field_lookup] = NumericRange(int(start), int(end), "[]")
        query_gt[gt_field_lookup] = NumericRange(int(start), int(end), "[]")
        lower_gene = GeneAssembly.objects.filter(**query_lt).order_by("-location").first()
        higher_gene = GeneAssembly.objects.filter(**query_gt).order_by("location").first()

        if lower_gene is None and higher_gene is None:
            return []

        if lower_gene is None:
            return higher_gene.gene.all()

        if higher_gene is None:
            return lower_gene.gene.all()

        lower_dist = start - lower_gene.location.lower
        higher_dist = higher_gene.location.lower - start
        if lower_dist > higher_dist:
            return higher_gene.gene.all()

        return lower_gene.gene.all()
