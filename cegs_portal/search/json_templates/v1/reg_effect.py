from typing import Any, NotRequired, Optional, TypedDict

from cegs_portal.search.models import RegulatoryEffectObservation

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
        "cell_lines": NotRequired[list[str]],
        "tissue_types": NotRequired[list[str]],
        "source_ids": list[str],
        "target_ids": list[Optional[str]],
        "co_regulators": NotRequired[list[int]],
        "co_sources": NotRequired[list[int]],
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
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "target_ids": [target.ensembl_id for target in reg_effect.targets.all()],
    }

    if reg_effect.experiment is not None:
        result["experiment"] = {"accession_id": reg_effect.experiment.accession_id, "name": reg_effect.experiment.name}

    if hasattr(reg_effect, "cell_lines"):
        result["cell_lines"] = [str(cl) for cl in reg_effect.cell_lines]

    if hasattr(reg_effect, "tissue_types"):
        result["tissue_types"] = [str(tt) for tt in reg_effect.tissue_types]

    if hasattr(reg_effect, "co_regulators"):
        result["co_regulators"] = [coreg.id for coreg in getattr(reg_effect, "co_regulators")]

    if hasattr(reg_effect, "co_sources"):
        result["co_sources"] = [cosrc.id for cosrc in getattr(reg_effect, "co_sources")]

    return result
