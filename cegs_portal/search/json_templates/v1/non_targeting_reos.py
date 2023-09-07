from typing import Any, Optional, TypedDict

from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import Pageable, PageableJson

ExperimentJson = TypedDict("ExperimentJson", {"accession_id": str, "name": str})
LocationJson = TypedDict("LocationJson", {"chromo": str, "strand": str, "lower": int, "upper": int})
SourceJson = TypedDict("SourceJson", {"accession_id": str, "location": LocationJson, "tss_distance": int, "type": str})
RegulatoryEffectObservationJson = TypedDict(
    "RegulatoryEffectObservationJson",
    {
        "accession_id": str,
        "experiment": ExperimentJson,
        "direction": str,
        "effect_size": Optional[float],
        "significance": Optional[float],
        "raw_p_value": Optional[float],
        "source_ids": list[SourceJson],
    },
)


def non_target_regulatory_effect(
    non_target_data: tuple[Pageable[RegulatoryEffectObservation], Any], options: Optional[dict[str, Any]] = None
) -> PageableJson:
    reg_effects, _ = non_target_data

    results: list[RegulatoryEffectObservationJson] = [
        {
            "accession_id": reg_effect.accession_id,
            "experiment": {"accession_id": reg_effect.experiment.accession_id, "name": reg_effect.experiment.name},
            "direction": reg_effect.direction,
            "effect_size": reg_effect.effect_size,
            "significance": reg_effect.significance,
            "raw_p_value": reg_effect.raw_p_value,
            "source_ids": [
                {
                    "accession_id": source.accesion_id,
                    "location": {
                        "chromo": source.chromo_name,
                        "strand": source.strand,
                        "lower": source.location.lower,
                        "upper": source.location.upper,
                    },
                    "tss_distance": source.closest_gene_distance,
                    "type": source.feature_type,
                }
                for source in reg_effect.sources.all()
            ],
        }
        for reg_effect in reg_effects
    ]

    return {
        "object_list": results,
        "page": reg_effects.number,
        "has_next_page": reg_effects.has_next(),
        "has_prev_page": reg_effects.has_previous(),
        "num_pages": reg_effects.paginator.num_pages,
    }
