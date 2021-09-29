from functools import singledispatch

from cegs_portal.search.models import (
    DNaseIHypersensitiveSite,
    Gene,
    GeneAssembly,
    RegulatoryEffect,
)


@singledispatch
def json(model, _json_format=None):
    return model


@json.register(DNaseIHypersensitiveSite)
def _(dhs_object, json_format=None):
    result = {
        "cell_line": dhs_object.cell_line,
        "start": dhs_object.location.lower,
        "end": dhs_object.location.upper,
        "closest_gene": json(dhs_object.closest_gene, json_format),
        "closest_gene_assembly": json(dhs_object.closest_gene_assembly, json_format),
        "closest_gene_id": dhs_object.closest_gene_id,
        "closest_gene_name": dhs_object.closest_gene_name,
        "ref_genome": dhs_object.ref_genome,
        "ref_genome_patch": dhs_object.ref_genome_patch,
    }

    if json_format == "genoverse":
        result["id"] = str(dhs_object.id)
        result["chr"] = dhs_object.chromosome_name.removeprefix("chr")
    else:
        result["id"] = dhs_object.id
        result["chr"] = dhs_object.chromosome_name

    return result


@json.register(RegulatoryEffect)
def _(reg_effect, json_format=None):
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction.value,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "targets": [target.ensemble_id for target in reg_effect.targets.all()],
    }


@json.register(GeneAssembly)
def _(gene_assembly, json_format=None):
    result = {
        "name": gene_assembly.name,
        "start": gene_assembly.location.lower,
        "end": gene_assembly.location.upper - 1,
        "strand": gene_assembly.strand,
        "ids": gene_assembly.ids,
        "ref_genome": gene_assembly.ref_genome,
        "ref_genome_patch": gene_assembly.ref_genome_patch,
    }

    if json_format == "genoverse":
        result["id"] = str(gene_assembly.id)
        result["chr"] = gene_assembly.chrom_name.removeprefix("chr")
    else:
        result["id"] = gene_assembly.id
        result["chr"] = gene_assembly.chrom_name

    return result


@json.register(Gene)
def _(gene_obj, json_format=None):
    return {
        "ensembl_id": gene_obj.ensembl_id,
        "type": gene_obj.gene_type,
    }
