def feature_exact(feature_obj):
    return {
        "id": feature_obj.ensembl_id,
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.ensembl_id if feature_obj.parent is not None else None,
        "misc": feature_obj.misc,
        "assemblies": [assembly(a) for a in feature_obj.assemblies.all()],
        "children": [children(c) for c in feature_obj.children.all()],
        "dhss": [dhs(d) for d in feature_obj.dnaregion_set.all()],
        "regulatory_effects": [reg_effect(r) for r in feature_obj.regulatory_effects.all()],
    }


def assembly(assembly_obj):
    return {
        "name": assembly_obj.name,
        "chrom": assembly_obj.chrom_name,
        "start": assembly_obj.location.lower,
        "end": assembly_obj.location.upper,
        "strand": assembly_obj.strand,
        "assembly": f"{assembly_obj.ref_genome}.{assembly_obj.ref_genome_patch or '0'}",
    }


def children(child_obj):
    return {
        "ensembl_id": child_obj.ensembl_id,
        "assemblies": [assembly(a) for a in child_obj.assemblies.all()],
    }


def dhs(dhs_obj):
    return {
        "id": dhs_obj.id,
        "cell_line": dhs_obj.cell_line,
        "chrom": dhs_obj.chromosome_name,
        "start": dhs_obj.location.lower,
        "end": dhs_obj.location.upper,
        "strand": dhs_obj.strand,
        "assembly": f"{dhs_obj.ref_genome}.{dhs_obj.ref_genome_patch or '0'}",
        "reg_effect_count": dhs_obj.regulatory_effects.count(),
    }


def reg_effect(re_obj):
    return {
        "id": re_obj.id,
        "effect_size": re_obj.effect_size,
        "direction": re_obj.direction,
        "significance": re_obj.significance,
        "experiment_id": re_obj.experiment_id,
        "source_ids": [dhs.id for dhs in re_obj.sources.all()],
    }
