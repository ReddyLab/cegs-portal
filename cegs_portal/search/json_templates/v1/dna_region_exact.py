from django.core.paginator import Page

from cegs_portal.search.json_templates.v1.reg_effect import regulatory_effect
from cegs_portal.search.models import DNARegion


def dnaregion(dnaregion: tuple[DNARegion, Page], json_format=None):
    region, reg_effects = dnaregion
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
