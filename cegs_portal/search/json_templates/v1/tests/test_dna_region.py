from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.dna_region import assembly as a_json
from cegs_portal.search.json_templates.v1.dna_region import dnaregion as dr_json
from cegs_portal.search.json_templates.v1.dna_region import dnaregions as drs_json
from cegs_portal.search.json_templates.v1.dna_region import feature_exact as fe_json
from cegs_portal.search.json_templates.v1.dna_region import regulatory_effect as re_json
from cegs_portal.search.models import (
    DNARegion,
    Feature,
    FeatureAssembly,
    RegulatoryEffect,
)

pytestmark = pytest.mark.django_db


def test_dna_region(region_tuple: tuple[DNARegion, Iterable]):
    region, reg_effects = region_tuple

    result = {
        "id": region.id,
        "chr": region.chromosome_name,
        "cell_line": region.cell_line,
        "start": region.location.lower,
        "end": region.location.upper,
        "closest_gene_id": region.closest_gene.id,
        "closest_gene_ensembl_id": region.closest_gene.ensembl_id,
        "closest_gene_assembly_id": region.closest_gene_assembly.id,
        "closest_gene_name": region.closest_gene_name,
        "ref_genome": region.ref_genome,
        "ref_genome_patch": region.ref_genome_patch,
        "effects": [re_json(effect) for effect in reg_effects],
        "facets": [value.value for value in region.facet_values.all()],
        "type": region.region_type,
    }

    if hasattr(region, "label"):
        result["label"] = region.label

    assert dr_json(region_tuple) == result

    result["id"] = str(region.id)
    result["chr"] = region.chromosome_name.removeprefix("chr")
    result["effects"] = [re_json(effect, json_format="genoverse") for effect in reg_effects]

    assert dr_json(region_tuple, json_format="genoverse") == result


def _dnaregion(region: DNARegion, reg_effects: Iterable[RegulatoryEffect], json_format: str = None):
    result = {
        "cell_line": region.cell_line,
        "start": region.location.lower,
        "end": region.location.upper,
        "closest_gene_id": region.closest_gene.id,
        "closest_gene_ensembl_id": region.closest_gene.ensembl_id,
        "closest_gene_assembly_id": region.closest_gene_assembly.id,
        "closest_gene_name": region.closest_gene_name,
        "ref_genome": region.ref_genome,
        "ref_genome_patch": region.ref_genome_patch,
        "effects": [re_json(effect, json_format) for effect in reg_effects],
        "facets": [value.value for value in region.facet_values.all()],
        "type": region.region_type,
    }

    if hasattr(region, "label"):
        result["label"] = region.label

    if json_format == "genoverse":
        result["id"] = str(region.id)
        result["chr"] = region.chromosome_name.removeprefix("chr")
    else:
        result["id"] = region.id
        result["chr"] = region.chromosome_name

    return result


def test_dna_regions(regions: list[DNARegion]):
    assert drs_json(regions) == [_dnaregion(region, region.regulatory_effects.all()) for region in regions]
    assert drs_json(regions, json_format="genoverse") == [
        _dnaregion(region, region.regulatory_effects.all(), json_format="genoverse") for region in regions
    ]


def test_regulatory_effect(reg_effect: RegulatoryEffect):
    result = {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "targets": [fe_json(target) for target in reg_effect.targets.all()],
        "target_assemblies": [a_json(target) for target in reg_effect.target_assemblies.all()],
    }

    assert re_json(reg_effect) == result

    result["targets"] = [fe_json(target, json_format="genoverse") for target in reg_effect.targets.all()]
    result["target_assemblies"] = [
        a_json(target, json_format="genoverse") for target in reg_effect.target_assemblies.all()
    ]

    assert re_json(reg_effect, json_format="genoverse") == result


def test_feature_exact(feature: Feature):
    result = {
        "id": feature.id,
        "ensembl_id": feature.ensembl_id,
        "type": feature.feature_type,
        "subtype": feature.feature_subtype,
        "parent_id": feature.parent.ensembl_id if feature.parent is not None else None,
        "misc": feature.misc,
    }
    assert fe_json(feature) == result

    result["id"] = str(feature.id)
    assert fe_json(feature, json_format="genoverse") == result


def test_assembly(assembly: FeatureAssembly):
    result = {
        "chr": assembly.chrom_name,
        "name": assembly.name,
        "start": assembly.location.lower,
        "end": assembly.location.upper,
        "strand": assembly.strand,
        "assembly": f"{assembly.ref_genome}.{assembly.ref_genome_patch or '0'}",
    }
    assert a_json(assembly) == result

    result["chr"] = assembly.chrom_name.removeprefix("chr")
    assert a_json(assembly, json_format="genoverse") == result
