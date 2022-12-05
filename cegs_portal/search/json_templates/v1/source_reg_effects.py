from typing import Any, Optional, TypedDict

from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import Pageable, PageableJson

ExperimentJson = TypedDict("ExperimentJson", {"id": int, "name": str})
RegulatoryEffectObservationJson = TypedDict(
    "RegulatoryEffectObservationJson",
    {
        "accession_id": str,
        "direction": str,
        "effect_size": Optional[float],
        "significance": Optional[float],
        "raw_p_value": Optional[float],
        "experiment": ExperimentJson,
        "source_ids": list[str],
        "target_ids": list[str],
    },
)


def regulatory_effect(
    reg_effect: RegulatoryEffectObservation, options: Optional[dict[str, Any]] = None
) -> RegulatoryEffectObservationJson:
    result = {
        "accession_id": reg_effect.accession_id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "experiment": {"id": reg_effect.experiment.id, "name": reg_effect.experiment.name},
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "target_ids": [target.ensembl_id for target in reg_effect.targets.all()],
    }

    return result


def source_reg_effects(
    reg_effects: Pageable[RegulatoryEffectObservation], options: Optional[dict[str, Any]] = None
) -> PageableJson:
    results = {
        "object_list": [regulatory_effect(re, options) for re in reg_effects.object_list],
        "page": reg_effects.number,
        "has_next_page": reg_effects.has_next(),
        "has_prev_page": reg_effects.has_previous(),
        "num_pages": reg_effects.paginator.num_pages,
    }

    return results
