import pytest

from cegs_portal.search.json_templates.v1.dna_feature import feature as f_json
from cegs_portal.search.json_templates.v1.dna_feature import reg_effect as re_json
from cegs_portal.search.json_templates.v1.dna_feature import region as r_json
from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation

pytestmark = pytest.mark.django_db


def test_feature(feature: DNAFeature):
    result = {
        "accession_id": feature.accession_id,
        "ensembl_id": feature.ensembl_id,
        "cell_line": feature.cell_line,
        "chr": feature.chrom_name,
        "name": feature.name,
        "start": feature.location.lower,
        "end": feature.location.upper,
        "strand": feature.strand,
        "closest_gene_ensembl_id": None,
        "closest_gene_name": feature.closest_gene_name,
        "assembly": f"{feature.ref_genome}.{feature.ref_genome_patch or '0'}",
        "type": feature.get_feature_type_display(),
        "subtype": feature.feature_subtype,
        "parent_id": feature.parent.ensembl_id if feature.parent is not None else None,
        "misc": feature.misc,
        "ids": feature.ids,
        "facets": [value.value for value in feature.facet_values.all()],
        "children": [f_json(c) for c in feature.children.all()],
        "closest_features": [r_json(d) for d in feature.closest_features.all()],
        "reg_effect_source_for": [re_json(r) for r in feature.source_for.all()],
        "reg_effect_target_of": [re_json(r) for r in feature.target_of.all()],
    }

    assert f_json(feature) == result

    result["chr"] = feature.chrom_name.removeprefix("chr")
    result["children"] = [f_json(c, {"json_format": "genoverse"}) for c in feature.children.all()]
    result["closest_features"] = [r_json(d, {"json_format": "genoverse"}) for d in feature.closest_features.all()]
    result["reg_effect_source_for"] = [re_json(r, {"json_format": "genoverse"}) for r in feature.source_for.all()]
    result["reg_effect_target_of"] = [re_json(r, {"json_format": "genoverse"}) for r in feature.target_of.all()]

    assert f_json(feature, {"json_format": "genoverse"}) == result


def test_region(feature: DNAFeature):
    result = {
        "accession_id": feature.accession_id,
        "chr": feature.chrom_name,
        "cell_line": feature.cell_line,
        "start": feature.location.lower,
        "end": feature.location.upper,
        "strand": feature.strand,
        "assembly": f"{feature.ref_genome}.{feature.ref_genome_patch or '0'}",
        "reg_effect_count": feature.source_for.count() + feature.target_of.count(),
    }

    assert r_json(feature) == result

    result["chr"] = feature.chrom_name.removeprefix("chr")

    assert r_json(feature, {"json_format": "genoverse"}) == result


def test_regulatory_effect(reg_effect: RegulatoryEffectObservation):
    result = {
        "accession_id": reg_effect.accession_id,
        "effect_size": reg_effect.effect_size,
        "direction": reg_effect.direction,
        "significance": reg_effect.significance,
        "experiment_id": reg_effect.experiment_accession_id,
        "source_ids": [dhs.id for dhs in reg_effect.sources.all()],
    }

    assert re_json(reg_effect) == result

    assert re_json(reg_effect, {"json_format": "genoverse"}) == result
