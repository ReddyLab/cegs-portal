from cegs_portal.search.models import DNARegion


def dnaregions(regions: list[DNARegion], json_format=None):
    return [dnaregion(region, json_format) for region in regions]


def dnaregion(region: DNARegion, json_format=None):
    result = {
        "cell_line": region.cell_line,
        "start": region.location.lower,
        "end": region.location.upper,
        "closest_gene_id": region.closest_gene.id,
        "closest_gene_assembly_id": region.closest_gene_assembly.id,
        "closest_gene_name": region.closest_gene_name,
        "ref_genome": region.ref_genome,
        "ref_genome_patch": region.ref_genome_patch,
        "effect_ids": [effect.id for effect in region.regulatory_effects.all()],
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
