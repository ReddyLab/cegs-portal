from typing import Iterable

from django.core.paginator import Page

from cegs_portal.search.models import (
    DNARegion,
    Feature,
    FeatureAssembly,
    RegulatoryEffect,
)


def dnaregions(regions: list[DNARegion], json_format: str = None):
    return [_dnaregion(region, region.regulatory_effects.all(), json_format) for region in regions]


def dnaregion(region: tuple[DNARegion, Page], json_format: str = None):
    return _dnaregion(region[0], region[1], json_format)


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
        "effects": [regulatory_effect(effect) for effect in reg_effects],
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


def regulatory_effect(reg_effect: RegulatoryEffect, json_format: str = None):
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "targets": [feature_exact(target, json_format) for target in reg_effect.targets.all()],
        "target_assemblies": [assembly(target, json_format) for target in reg_effect.targets.all()],
    }


def feature_exact(feature_obj: Feature, json_format: str = None):
    result = {
        "ensembl_id": feature_obj.ensembl_id,
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.ensembl_id if feature_obj.parent is not None else None,
        "misc": feature_obj.misc,
    }

    if json_format == "genoverse":
        result["id"] = str(feature_obj.id)
    else:
        result["id"] = feature_obj.id

    return result


def assembly(assembly_obj: FeatureAssembly, json_format: str = None):
    result = {
        "name": assembly_obj.name,
        "start": assembly_obj.location.lower,
        "end": assembly_obj.location.upper,
        "strand": assembly_obj.strand,
        "assembly": f"{assembly_obj.ref_genome}.{assembly_obj.ref_genome_patch or '0'}",
    }

    if json_format == "genoverse":
        result["chr"] = assembly_obj.chrom_name.removeprefix("chr")
    else:
        result["chr"] = assembly_obj.chrom_name

    return result
