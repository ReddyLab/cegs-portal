import pytest

from cegs_portal.search.json_templates.v1.source_reg_effects import (
    PageableJson,
)
from cegs_portal.search.json_templates.v1.source_reg_effects import source_reg_effect as re_json
from cegs_portal.search.models import RegulatoryEffectObservation


pytestmark = pytest.mark.django_db


def test_regulatory_effect(reg_effect: RegulatoryEffectObservation):

    result: PageableJson = {
        "accession_id": reg_effect.accession_id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
    }

    assert re_json(reg_effect) == result
    assert re_json(reg_effect, {"json_format": "genoverse"}) == result
