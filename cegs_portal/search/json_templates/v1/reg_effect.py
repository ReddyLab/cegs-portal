from typing import Optional, TypedDict

from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import Pageable

ExperimentJson = TypedDict("ExperimentJson", {"id": int, "name": str})
RegulatoryEffectObservationJson = TypedDict(
    "RegulatoryEffectObservationJson",
    {
        "id": int,
        "direction": str,
        "effect_size": Optional[float],
        "significance": Optional[float],
        "raw_p_value": Optional[float],
        "experiment": ExperimentJson,
        "cell_lines": list[str],
        "tissue_types": list[str],
        "source_ids": list[str],
        "target_ids": list[str],
        "co_regulators": Optional[list[int]],
        "co_sources": Optional[list[int]],
    },
)


def regulatory_effect(
    reg_effect: RegulatoryEffectObservation, json_format: str = None
) -> RegulatoryEffectObservationJson:
    result = {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "experiment": {"id": reg_effect.experiment.id, "name": reg_effect.experiment.name},
        "cell_lines": [str(cl) for cl in reg_effect.cell_lines],  # type: ignore[attr-defined]
        "tissue_types": [str(tt) for tt in reg_effect.tissue_types],  # type: ignore[attr-defined]
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "target_ids": [target.ensembl_id for target in reg_effect.targets.all()],
        "co_regulators": None,
        "co_sources": None,
    }

    if hasattr(reg_effect, "co_regulators"):
        result["co_regulators"] = [coreg.id for coreg in getattr(reg_effect, "co_regulators")]

    if hasattr(reg_effect, "co_sources"):
        result["co_sources"] = [cosrc.id for cosrc in getattr(reg_effect, "co_sources")]

    return result


def source_reg_effects(reg_effects: Pageable[RegulatoryEffectObservation], json_format: str = None):
    results = {
        "objects": [regulatory_effect(re, json_format) for re in reg_effects.object_list],
        "page": reg_effects.number,
        "has_next_page": reg_effects.has_next(),
        "has_prev_page": reg_effects.has_previous(),
        "num_pages": reg_effects.paginator.num_pages,
    }

    return results
