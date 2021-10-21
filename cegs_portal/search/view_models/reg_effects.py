from enum import Enum
from typing import Optional

from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNARegion
from cegs_portal.search.view_models.errors import ViewModelError


class LocSearchType(Enum):
    EXACT = "exact"
    OVERLAP = "overlap"


class DHSSearch:
    @classmethod
    def id_search(cls, dhs_id: str):
        dhs = DNARegion.objects.get(id=dhs_id, region_type="dhs")
        return dhs

    @classmethod
    def loc_search(
        cls,
        chromo: str,
        start: str,
        end: str,
        assembly: str,
        search_type: str,
        region_types: Optional[list[str]] = None,
    ):
        query = {"chromosome_name": chromo}
        field = "location"
        if search_type == LocSearchType.OVERLAP.value:
            field += "__overlap"
        elif search_type == LocSearchType.EXACT.value:
            pass
        else:
            raise ViewModelError(f"Invalid search type: {search_type}")

        if assembly is not None:
            query["ref_genome"] = assembly

        if region_types is not None:
            query["region_type__in"] = region_types

        query[field] = NumericRange(int(start), int(end), "[]")
        genes = (
            DNARegion.objects.filter(**query)
            .select_related(
                "closest_gene", "closest_gene_assembly", "closest_gene_assembly__feature", "closest_gene__parent"
            )
            .distinct()
        )
        return genes
