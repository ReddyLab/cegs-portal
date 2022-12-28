from typing import Any, NotRequired, Optional, TypedDict

from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import Pageable, PageableJson

ExperimentJson = TypedDict("ExperimentJson", {"accession_id": str, "name": str})
RegulatoryEffectObservationJson = TypedDict(
    "RegulatoryEffectObservationJson",
    {
        "accession_id": str,
        "direction": str,
        "effect_size": Optional[float],
        "significance": Optional[float],
        "raw_p_value": Optional[float],
        "experiment": NotRequired[ExperimentJson],
        "source_ids": list[str],
        "target_ids": list[str],
    },
)


def regulatory_effect(
    reg_effect: RegulatoryEffectObservation, options: Optional[dict[str, Any]] = None
) -> RegulatoryEffectObservationJson:
    result: RegulatoryEffectObservationJson = {
        "accession_id": reg_effect.accession_id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "source_ids": [source.accession_id for source in reg_effect.sources.all()],
        "target_ids": [target.accession_id for target in reg_effect.targets.all()],
    }

    if reg_effect.experiment is not None:
        result["experiment"] = {"accession_id": reg_effect.experiment.accession_id, "name": reg_effect.experiment.name}

    return result


def feature_reg_effects(
    reg_effects: Pageable[RegulatoryEffectObservation], options: Optional[dict[str, Any]] = None
) -> PageableJson:
    results: PageableJson = {
        "object_list": [regulatory_effect(re, options) for re in reg_effects.object_list],
        "page": reg_effects.number,
        "has_next_page": reg_effects.has_next(),
        "has_prev_page": reg_effects.has_previous(),
        "num_pages": reg_effects.paginator.num_pages,
    }

    return results
