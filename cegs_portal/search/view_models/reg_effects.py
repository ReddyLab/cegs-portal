from enum import Enum

from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNaseIHypersensitiveSite, RegulatoryEffect
from cegs_portal.search.view_models.errors import ViewModelError


class LocSearchType(Enum):
    EXACT = "exact"
    OVERLAP = "overlap"


class DHSSearch:
    @classmethod
    def id_search(cls, dhs_id):
        dhs = DNaseIHypersensitiveSite.objects.get(id=dhs_id)
        return dhs

    @classmethod
    def loc_search(cls, chromo, start, end, assembly, search_type):
        query = {"chromosome_name": chromo}
        field = "location"
        if search_type == LocSearchType.OVERLAP.value:
            field += "__overlap"
        else:
            raise ViewModelError(f"Invalid search type: {search_type}")

        if assembly is not None:
            query["ref_genome"] = assembly

        query[field] = NumericRange(int(start), int(end), "[]")
        genes = RegulatoryEffect.objects.filter(**query).distinct()
        return genes
