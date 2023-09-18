import pytest

from cegs_portal.search.json_templates.v1.non_targeting_reos import (
    RegulatoryEffectObservationJson,
)
from cegs_portal.search.json_templates.v1.non_targeting_reos import (
    non_targeting_regulatory_effects as ntre_json,
)
from cegs_portal.search.json_templates.v1.non_targeting_reos import (
    regulatory_effect as re_json,
)
from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import MockPaginator

pytestmark = pytest.mark.django_db


def test_non_targeting_regulatory_effects(sig_only_source_reg_effects):
    feature = sig_only_source_reg_effects["source"]
    reo_pager = MockPaginator(sig_only_source_reg_effects["effects"], 2)
    reo_page = reo_pager.get_page(1)
    result = {
        "object_list": [re_json(reo) for reo in reo_page.object_list],
        "page": 1,
        "has_next_page": True,
        "has_prev_page": False,
        "num_pages": 2,
    }
    assert ntre_json((reo_page, feature)) == result


def test_regulatory_effect(reg_effect: RegulatoryEffectObservation):
    assert reg_effect.experiment is not None

    result: RegulatoryEffectObservationJson = {
        "accession_id": reg_effect.accession_id,
        "experiment": {"accession_id": reg_effect.experiment.accession_id, "name": reg_effect.experiment.name},
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "source_ids": [
            {
                "accession_id": source.accession_id,
                "location": {
                    "chromo": source.chrom_name,
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

    assert re_json(reg_effect) == result
