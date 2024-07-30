from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.dna_features import feature as f_json
from cegs_portal.search.json_templates.v1.dna_features import features as fs_json
from cegs_portal.search.json_templates.v1.dna_features import reg_effect as re_json
from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation

pytestmark = pytest.mark.django_db


def test_features(features: Iterable[DNAFeature]):
    result = [f_json(a) for a in features]

    assert fs_json(features) == result

    result = [f_json(a, {"json_format": "genoverse"}) for a in features]

    assert fs_json(features, {"json_format": "genoverse"}) == result


def test_feature(feature: DNAFeature, effect_dir_feature: DNAFeature):
    result = {
        "accession_id": feature.accession_id,
        "ensembl_id": feature.ensembl_id,
        "closest_gene_name": feature.closest_gene_name,
        "closest_gene_ensembl_id": None,
        "cell_line": feature.cell_line,
        "chr": feature.chrom_name,
        "name": feature.name,
        "start": feature.location.lower,
        "end": feature.location.upper - 1,
        "strand": feature.strand,
        "ids": feature.ids,
        "type": feature.get_feature_type_display(),
        "subtype": feature.feature_subtype,
        "ref_genome": feature.ref_genome,
        "parent": feature.parent if feature.parent is not None else None,
        "parent_accession_id": feature.parent_accession_id if feature.parent is not None else None,
        "parent_ensembl_id": feature.parent_ensembl_id if feature.parent is not None else None,
        "misc": feature.misc,
    }
    if feature.closest_gene is not None:
        result["closest_gene_ensembl_id"] = feature.closest_gene_ensembl_id

    f_dict = f_json(feature)
    assert f_dict == result

    assert "source_for" not in f_dict
    assert "target_of" not in f_dict
    assert "effect_directions" not in f_dict

    f_dict = f_json(feature, {"feature_properties": ["regeffects"]})
    assert "source_for" in f_dict
    assert "target_of" in f_dict

    f_dict = f_json(effect_dir_feature, {"feature_properties": ["effect_directions"]})
    assert "effect_directions" in f_dict

    result["id"] = result["accession_id"]
    result["chr"] = feature.chrom_name.removeprefix("chr")
    assert f_json(feature, {"json_format": "genoverse"}) == result


def test_reg_effect(reg_effect: RegulatoryEffectObservation):
    result = {
        "accession_id": reg_effect.accession_id,
        "effect_size": reg_effect.effect_size,
        "direction": reg_effect.direction,
        "significance": reg_effect.significance,
        "experiment_id": reg_effect.experiment_accession_id,
        "sources": [{"name": feature.name, "ensembl_id": feature.ensembl_id} for feature in reg_effect.sources.all()],
        "targets": [{"name": feature.name, "ensembl_id": feature.ensembl_id} for feature in reg_effect.targets.all()],
    }

    assert re_json(reg_effect) == result
    result["id"] = result["accession_id"]
    assert re_json(reg_effect, {"json_format": "genoverse"}) == result
