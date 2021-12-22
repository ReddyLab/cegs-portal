def feature_exact(feature_obj, json_format=None):
    result = {
        "ensembl_id": feature_obj.ensembl_id,
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.ensembl_id if feature_obj.parent is not None else None,
        "misc": feature_obj.misc,
        "assemblies": [assembly(a, json_format) for a in feature_obj.assemblies.all()],
        "children": [children(c, json_format) for c in feature_obj.children.all()],
        "dhss": [dhs(d, json_format) for d in feature_obj.dnaregion_set.all()],
        "regulatory_effects": [reg_effect(r, json_format) for r in feature_obj.regulatory_effects.all()],
    }

    if json_format == "genoverse":
        result["id"] = str(feature_obj.id)
    else:
        result["id"] = feature_obj.id

    return result


def assembly(assembly_obj, json_format=None):
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


def children(child_obj, json_format=None):
    return {
        "ensembl_id": child_obj.ensembl_id,
        "assemblies": [assembly(a, json_format) for a in child_obj.assemblies.all()],
    }


def dhs(dhs_obj, json_format=None):
    result = {
        "cell_line": dhs_obj.cell_line,
        "start": dhs_obj.location.lower,
        "end": dhs_obj.location.upper,
        "strand": dhs_obj.strand,
        "assembly": f"{dhs_obj.ref_genome}.{dhs_obj.ref_genome_patch or '0'}",
        "reg_effect_count": dhs_obj.regulatory_effects.count(),
    }

    if json_format == "genoverse":
        result["id"] = str(dhs_obj.id)
        result["chr"] = dhs_obj.chrom_name.removeprefix("chr")
    else:
        result["id"] = dhs_obj.id
        result["chr"] = dhs_obj.chrom_name

    return result


def reg_effect(re_obj, json_format=None):
    result = {
        "id": re_obj.id,
        "effect_size": re_obj.effect_size,
        "direction": re_obj.direction,
        "significance": re_obj.significance,
        "experiment_id": re_obj.experiment_id,
        "source_ids": [dhs.id for dhs in re_obj.sources.all()],
    }

    if json_format == "genoverse":
        result["id"] = str(re_obj.id)
    else:
        result["id"] = re_obj.id
