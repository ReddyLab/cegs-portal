import pytest

from cegs_portal.search.json_templates.v1.feature_exact import assembly as a_json
from cegs_portal.search.json_templates.v1.feature_exact import children as c_json
from cegs_portal.search.json_templates.v1.feature_exact import reg_effect as re_json
from cegs_portal.search.json_templates.v1.feature_exact import region as r_json
from cegs_portal.search.models import DNARegion, FeatureAssembly, RegulatoryEffect

pytestmark = pytest.mark.django_db


def test_assembly(assembly: FeatureAssembly):
    result = {
        "id": assembly.id,
        "ensembl_id": assembly.ensembl_id,
        "chr": assembly.chrom_name,
        "name": assembly.name,
        "start": assembly.location.lower,
        "end": assembly.location.upper,
        "strand": assembly.strand,
        "assembly": f"{assembly.ref_genome}.{assembly.ref_genome_patch or '0'}",
        "type": assembly.feature_type,
        "subtype": assembly.feature_subtype,
        "parent_id": assembly.parent.ensembl_id if assembly.parent is not None else None,
        "misc": assembly.misc,
        "children": [c_json(c) for c in assembly.children.all()],
        "closest_regions": [r_json(d) for d in assembly.dnaregion_set.all()],
        "regulatory_effects": [re_json(r) for r in assembly.regulatory_effects.all()],
    }

    assert a_json(assembly) == result

    result["id"] = str(assembly.id)
    result["chr"] = assembly.chrom_name.removeprefix("chr")
    result["children"] = [c_json(c, json_format="genoverse") for c in assembly.children.all()]
    result["closest_regions"] = [r_json(d, json_format="genoverse") for d in assembly.dnaregion_set.all()]
    result["regulatory_effects"] = [re_json(r, json_format="genoverse") for r in assembly.regulatory_effects.all()]

    assert a_json(assembly, json_format="genoverse") == result


def test_region(region: DNARegion):
    result = {
        "id": region.id,
        "chr": region.chrom_name,
        "cell_line": region.cell_line,
        "start": region.location.lower,
        "end": region.location.upper,
        "strand": region.strand,
        "assembly": f"{region.ref_genome}.{region.ref_genome_patch or '0'}",
        "reg_effect_count": region.regulatory_effects.count(),
    }

    assert r_json(region) == result

    result["id"] = str(region.id)
    result["chr"] = region.chrom_name.removeprefix("chr")

    assert r_json(region, json_format="genoverse") == result


def test_regulatory_effect(reg_effect: RegulatoryEffect):
    result = {
        "id": reg_effect.id,
        "effect_size": reg_effect.effect_size,
        "direction": reg_effect.direction,
        "significance": reg_effect.significance,
        "experiment_id": reg_effect.experiment_id,
        "source_ids": [dhs.id for dhs in reg_effect.sources.all()],
    }

    assert re_json(reg_effect) == result

    result["id"] = str(reg_effect.id)

    assert re_json(reg_effect, json_format="genoverse") == result
