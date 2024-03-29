import pytest

from cegs_portal.search.json_templates.v1.reg_effect import (
    RegulatoryEffectObservationJson,
)
from cegs_portal.search.json_templates.v1.reg_effect import regulatory_effect as re_json
from cegs_portal.search.models import RegulatoryEffectObservation

pytestmark = pytest.mark.django_db


def test_regulatory_effect(reg_effect: RegulatoryEffectObservation):
    cell_lines: set[str] = set()
    tissue_types: set[str] = set()

    if reg_effect.experiment is not None:
        for bios in reg_effect.experiment.biosamples.all():
            cell_lines.add(bios.cell_line_name)
            tissue_types.add(bios.cell_line.tissue_type_name)

    setattr(reg_effect, "cell_lines", cell_lines)
    setattr(reg_effect, "tissue_types", tissue_types)

    assert reg_effect.experiment is not None

    result: RegulatoryEffectObservationJson = {
        "accession_id": reg_effect.accession_id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "cell_lines": [str(cl) for cl in reg_effect.cell_lines],  # type: ignore[attr-defined]
        "tissue_types": [str(tt) for tt in reg_effect.tissue_types],  # type: ignore[attr-defined]
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "target_ids": [target.ensembl_id for target in reg_effect.targets.all()],
        "experiment": {"accession_id": reg_effect.experiment.accession_id, "name": reg_effect.experiment.name},
    }

    assert len(result["cell_lines"]) == 1
    assert len(result["tissue_types"]) == 1
    assert re_json(reg_effect) == result
