from typing import Optional, TypedDict

from cegs_portal.search.models import RegulatoryEffect

RegulatoryEffectJson = TypedDict(
    "RegulatoryEffectJson",
    {
        "id": int,
        "direction": str,
        "effect_size": Optional[float],
        "significance": Optional[float],
        "raw_p_value": Optional[float],
        "cell_lines": list[str],
        "tissue_types": list[str],
        "source_ids": list[str],
        "target_ids": list[str],
    },
)


def regulatory_effect(reg_effect: RegulatoryEffect, json_format: str = None) -> RegulatoryEffectJson:
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "cell_lines": [str(cl) for cl in reg_effect.cell_lines],  # type: ignore[attr-defined]
        "tissue_types": [str(tt) for tt in reg_effect.tissue_types],  # type: ignore[attr-defined]
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "target_ids": [target.ensembl_id for target in reg_effect.targets.all()],
    }
