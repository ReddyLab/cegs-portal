from typing import Iterable

from cegs_portal.search.models import DNARegion, FeatureAssembly, RegulatoryEffect
from cegs_portal.utils.pagination_types import Pageable


def dnaregions(regions: Pageable[DNARegion], json_format: str = None):
    results = {
        "objects": [_dnaregion(region, region.regulatory_effects.all(), json_format) for region in regions.object_list],
        "page": regions.number,
        "has_next_page": regions.has_next(),
        "has_prev_page": regions.has_previous(),
        "num_pages": regions.paginator.num_pages,
    }

    return results


def dnaregion(region: tuple[DNARegion, Iterable], json_format: str = None):
    return _dnaregion(region[0], region[1], json_format)


def _dnaregion(region: DNARegion, reg_effects: Iterable[RegulatoryEffect], json_format: str = None):
    result = {
        "cell_line": region.cell_line,
        "start": region.location.lower,
        "end": region.location.upper,
        "closest_gene_ensembl_id": None,
        "closest_gene_assembly_id": None,
        "closest_gene_name": region.closest_gene_name,
        "ref_genome": region.ref_genome,
        "ref_genome_patch": region.ref_genome_patch,
        "effects": [regulatory_effect(effect) for effect in reg_effects],
        "facets": [value.value for value in region.facet_values.all()],
        "type": region.region_type,
    }

    if region.closest_gene_assembly is not None:
        result["closest_gene_ensembl_id"] = region.closest_gene_assembly.ensembl_id
        result["closest_gene_assembly_id"] = region.closest_gene_assembly.id

    if hasattr(region, "label"):
        result["label"] = region.label  # type: ignore[attr-defined]

    if json_format == "genoverse":
        result["id"] = str(region.id)
        result["chr"] = region.chrom_name.removeprefix("chr")
    else:
        result["id"] = region.id
        result["chr"] = region.chrom_name

    return result


def regulatory_effect(reg_effect: RegulatoryEffect, json_format: str = None):
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "target_assemblies": [assembly(target, json_format) for target in reg_effect.target_assemblies.all()],
    }


def assembly(assembly_obj: FeatureAssembly, json_format: str = None):
    result = {
        "ensembl_id": assembly_obj.ensembl_id,
        "name": assembly_obj.name,
        "start": assembly_obj.location.lower,
        "end": assembly_obj.location.upper,
        "strand": assembly_obj.strand,
        "assembly": f"{assembly_obj.ref_genome}.{assembly_obj.ref_genome_patch or '0'}",
        "type": assembly_obj.feature_type,
        "subtype": assembly_obj.feature_subtype,
        "parent_id": assembly_obj.parent.ensembl_id if assembly_obj.parent is not None else None,
        "misc": assembly_obj.misc,
    }

    if json_format == "genoverse":
        result["id"] = str(assembly_obj.id)
        result["chr"] = assembly_obj.chrom_name.removeprefix("chr")
    else:
        result["id"] = assembly_obj.id
        result["chr"] = assembly_obj.chrom_name

    return result
