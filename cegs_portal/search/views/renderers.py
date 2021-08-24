from functools import singledispatch

from cegs_portal.search.models import (
    DNaseIHypersensitiveSite,
    Gene,
    GeneAssembly,
    RegulatoryEffect,
)


def genoverse_reformat(json_dict):
    if value := json_dict.get("id", False):
        json_dict["id"] = str(value)

    if chromo := json_dict.get("chr", False):
        json_dict["chr"] = chromo.removeprefix("chr")


@singledispatch
def json(model):
    return model


@json.register(DNaseIHypersensitiveSite)
def _(dhs_object):
    return {
        "id": dhs_object.id,
        "cell_line": dhs_object.cell_line,
        "chr": dhs_object.chromosome_name,
        "start": dhs_object.location.lower,
        "end": dhs_object.location.upper,
        "strand": dhs_object.strand,
        "closest_gene": dhs_object.closest_gene_id,
        "closest_gene_name": dhs_object.closest_gene_name,
        "ref_genome": dhs_object.ref_genome,
        "ref_genome_patch": dhs_object.ref_genome_patch,
        "regulatory_effects": [json(effect) for effect in dhs_object.regulatory_effects.all()],
    }


@json.register(RegulatoryEffect)
def _(reg_effect):
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "score": reg_effect.score,
        "significance": reg_effect.significance,
        "targets": [target.ensemble_id for target in reg_effect.targets.all()],
    }


@json.register(GeneAssembly)
def _(gene_assembly):
    return {
        "name": gene_assembly.name,
        "chr": gene_assembly.chrom_name,
        "start": gene_assembly.location.lower,
        "end": gene_assembly.location.upper - 1,
        "strand": gene_assembly.strand,
        "ids": gene_assembly.ids,
        "ref_genome": gene_assembly.ref_genome,
        "ref_genome_patch": gene_assembly.ref_genome_patch,
    }


@json.register(Gene)
def _(gene_obj):
    return {
        "ensembl_id": gene_obj.ensembl_id,
        "type": gene_obj.gene_type,
        "locations": [json(assembly) for assembly in gene_obj.assemblies.all()],
    }
