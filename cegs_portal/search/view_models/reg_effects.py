from enum import Enum
from functools import reduce
from itertools import combinations_with_replacement
from typing import Optional

from django.db.models import Prefetch
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNARegion
from cegs_portal.search.models.reg_effects import RegulatoryEffect
from cegs_portal.search.view_models.errors import ViewModelError

LABEL_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def label_gen() -> list[str]:
    labels = []
    for i in range(1, 3):
        labels.extend(["".join(combo) for combo in combinations_with_replacement(LABEL_LETTERS, i)])

    return labels


LABELS = label_gen()
LABELS_LEN = len(LABELS)


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
        region_properties: str,
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

        query[field] = NumericRange(int(start), int(end), "[)")
        sig_effects = RegulatoryEffect.objects.exclude(direction__exact="non_sig").prefetch_related(
            "targets",
            "targets__parent",
            "target_assemblies",
            "target_assemblies__feature",
            "target_assemblies__feature__parent",
        )
        dna_regions = (
            DNARegion.objects.filter(**query)
            .select_related(
                "closest_gene",
                "closest_gene__parent",
                "closest_gene_assembly",
                "closest_gene_assembly__feature",
                "closest_gene_assembly__feature__parent",
            )
            .prefetch_related(
                Prefetch("regulatory_effects", queryset=sig_effects),
            )
            .distinct()
        )

        if region_properties is not None:
            if "reg_effect" in region_properties:
                dna_regions = [region for region in dna_regions if len(region.regulatory_effects.all()) > 0]
            if "effect_label" in region_properties:
                for region in dna_regions:
                    reg_effects = region.regulatory_effects.all()
                    if (
                        len(reg_effects) > 0
                        and reduce(lambda acc, effect: acc + len(effect.targets.all()), reg_effects, 0) > 0
                    ):
                        setattr(region, "label", LABELS[f"{region}".__hash__() % LABELS_LEN])

        return dna_regions
