import pytest

from cegs_portal.search.json_templates.v1.feature_reg_effects import (
    feature_reg_effects,
    regulatory_effect,
)
from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import Pageable

pytestmark = pytest.mark.django_db


def test_source_reg_effect(paged_source_reg_effects: Pageable[RegulatoryEffectObservation]):
    reg_effects = paged_source_reg_effects

    results = {
        "object_list": [regulatory_effect(re) for re in reg_effects.object_list],
        "page": reg_effects.number,
        "has_next_page": reg_effects.has_next(),
        "has_prev_page": reg_effects.has_previous(),
        "num_pages": reg_effects.paginator.num_pages,
    }

    assert feature_reg_effects(paged_source_reg_effects) == results
    assert feature_reg_effects(paged_source_reg_effects, {"json_format": "genoverse"}) == results


def test_regulatory_effect(reg_effect: RegulatoryEffectObservation):
    assert reg_effect.experiment is not None

    results = {
        "accession_id": reg_effect.accession_id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "experiment": {"accession_id": reg_effect.experiment.accession_id, "name": reg_effect.experiment.name},
        "source_ids": [source.accession_id for source in reg_effect.sources.all()],
        "target_ids": [target.accession_id for target in reg_effect.targets.all()],
    }

    assert regulatory_effect(reg_effect) == results
    assert regulatory_effect(reg_effect, {"json_format": "genoverse"}) == results
