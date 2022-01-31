from functools import singledispatch

from django.db.models import QuerySet

from cegs_portal.search.models import (
    DNARegion,
    Experiment,
    Facet,
    FacetValue,
    Feature,
    FeatureAssembly,
    RegulatoryEffect,
)
from cegs_portal.search.models.utils import ChromosomeLocation


@singledispatch
def json(model, json_format=None):
    if isinstance(model, QuerySet):  # type: ignore[misc]
        return [json(item, json_format) for item in model.all()]

    if isinstance(model, list):
        return [json(item, json_format) for item in model]

    if isinstance(model, dict):
        return {key: json(model[key], json_format) for key in model}

    return model


@json.register(ChromosomeLocation)
def _chromosomelocation(loc: ChromosomeLocation, json_format=None):
    return {"chromo": loc.chromo, "start": loc.range.lower, "end": loc.range.upper}


@json.register(Facet)
def _facet(fac: Facet, json_format=None):
    return {
        "name": fac.name,
        "description": fac.description,
        "values": [json(value, json_format) for value in fac.values.all()],
    }


@json.register(FacetValue)
def _facetvalue(val: FacetValue, json_format=None):
    return {"id": val.id, "value": val.value}


@json.register(DNARegion)
def _dnaregion(dnaregion: DNARegion, json_format=None):
    result = {
        "cell_line": dnaregion.cell_line,
        "start": dnaregion.location.lower,
        "end": dnaregion.location.upper,
        "closest_gene": json(dnaregion.closest_gene, json_format),
        "closest_gene_assembly": json(dnaregion.closest_gene_assembly, json_format),
        "closest_gene_id": dnaregion.closest_gene_id,
        "closest_gene_name": dnaregion.closest_gene_name,
        "ref_genome": dnaregion.ref_genome,
        "ref_genome_patch": dnaregion.ref_genome_patch,
        "effects": [json(effect, json_format) for effect in dnaregion.regulatory_effects.all()],
        "facet_values": {value.id: value.value for value in dnaregion.facet_values.all()},
        "type": dnaregion.region_type,
    }

    if hasattr(dnaregion, "label"):
        result["label"] = dnaregion.label  # type: ignore[attr-defined]

    if json_format == "genoverse":
        result["id"] = str(dnaregion.id)
        result["chr"] = dnaregion.chromosome_name.removeprefix("chr")
    else:
        result["id"] = dnaregion.id
        result["chr"] = dnaregion.chromosome_name

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


@json.register(Experiment)
def _experiment(experiment_obj, json_format=None):
    return {"id": experiment_obj.id, "name": experiment_obj.name}
