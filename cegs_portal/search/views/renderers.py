from functools import singledispatch

from django.db.models import QuerySet

from cegs_portal.search.models import (
    DNAFeature,
    Experiment,
    Facet,
    FacetValue,
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


@json.register(DNAFeature)
def _dnaregion(feature: DNAFeature, json_format=None):
    result = {
        "id": feature.feature.ensembl_id,
        "ids": feature.ids,
        "name": feature.name,
        "cell_line": feature.cell_line,
        "start": feature.location.lower,
        "end": feature.location.upper,
        "strand": feature.strand,
        "closest_gene": json(feature.closest_gene, json_format),
        "closest_gene_name": feature.closest_gene_name,
        "ref_genome": feature.ref_genome,
        "ref_genome_patch": feature.ref_genome_patch,
        "effects": [json(effect, json_format) for effect in feature.regulatory_effects.all()],
        "facet_values": {value.id: value.value for value in feature.facet_values.all()},
        "type": feature.get_feature_type_display(),
        "subtype": feature.feature_subtype,
        "parent_id": feature.parent.ensembl_id if feature.parent is not None else None,
        "misc": feature.misc,
    }

    if hasattr(feature, "label"):
        result["label"] = feature.label  # type: ignore[attr-defined]

    if json_format == "genoverse":
        result["id"] = str(feature.id)
        result["chr"] = feature.chrom_name.removeprefix("chr")
    else:
        result["id"] = feature.id
        result["chr"] = feature.chrom_name

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


@json.register(Experiment)
def _experiment(experiment_obj, json_format=None):
    return {"id": experiment_obj.id, "name": experiment_obj.name}
