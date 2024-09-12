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
        "sources": list[tuple[str, str, tuple[int, int, str], str]],
        "targets": list[tuple[str, str]],
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
        "sources": [
            (
                source.accession_id,
                source.chrom_name,
                (source.location.lower, source.location.upper, source.strand),
                source.get_feature_type_display(),
            )
            for source in reg_effect.sources.all()
        ],
        "targets": [(target.accession_id, target.name) for target in reg_effect.targets.all()],
    }

    if reg_effect.experiment is not None:
        result["experiment"] = {
            "accession_id": reg_effect.experiment.accession_id,
            "name": reg_effect.experiment.name,
            "type": reg_effect.experiment.experiment_type,
        }

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
