from functools import singledispatch

from cegs_portal.search.models import (
    DNARegion,
    Feature,
    FeatureAssembly,
    RegulatoryEffect,
)


@singledispatch
def json(model, _json_format=None):
    return model


@json.register(DNARegion)
def _dnaregion(dhs_object: DNARegion, json_format=None):
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
        "effects": [json(effect, json_format) for effect in dhs_object.regulatory_effects.all()],
    }

    if hasattr(dhs_object, "label"):
        result["label"] = dhs_object.label

    if json_format == "genoverse":
        result["id"] = str(dhs_object.id)
        result["chr"] = dhs_object.chromosome_name.removeprefix("chr")
    else:
        result["id"] = dhs_object.id
        result["chr"] = dhs_object.chromosome_name

    return result


@json.register(RegulatoryEffect)
def _regulatory_effect(reg_effect, json_format=None):
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "targets": [json(target, json_format) for target in reg_effect.targets.all()],
        "target_assemblies": [json(assembly, json_format) for assembly in reg_effect.target_assemblies.all()],
    }


@json.register(FeatureAssembly)
def _feature_assembly(feature_assembly, json_format=None):
    result = {
        "id": feature_assembly.feature.ensembl_id,
        "name": feature_assembly.name,
        "start": feature_assembly.location.lower,
        "end": feature_assembly.location.upper - 1,
        "strand": feature_assembly.strand,
        "ids": feature_assembly.ids,
        "ref_genome": feature_assembly.ref_genome,
        "ref_genome_patch": feature_assembly.ref_genome_patch,
        "feature": json(feature_assembly.feature, json_format),
    }

    if json_format == "genoverse":
        result["chr"] = feature_assembly.chrom_name.removeprefix("chr")
    else:
        result["chr"] = feature_assembly.chrom_name

    return result


@json.register(Feature)
def _feature(feature_obj, json_format=None):
    return {
        "id": feature_obj.ensembl_id,
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.ensembl_id if feature_obj.parent is not None else None,
        "misc": feature_obj.misc,
    }
