from cegs_portal.search.models import (
    DNARegion,
    Feature,
    FeatureAssembly,
    RegulatoryEffect,
)


def feature_exact(feature_obj: Feature, json_format: bool = None):
    result = {
        "ensembl_id": feature_obj.ensembl_id,
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.ensembl_id if feature_obj.parent is not None else None,
        "misc": feature_obj.misc,
        "assemblies": [assembly(a, json_format) for a in feature_obj.assemblies.all()],
        "children": [children(c, json_format) for c in feature_obj.children.all()],
        "closest_regions": [region(d, json_format) for d in feature_obj.dnaregion_set.all()],
        "regulatory_effects": [reg_effect(r, json_format) for r in feature_obj.regulatory_effects.all()],
    }

    if json_format == "genoverse":
        result["id"] = str(feature_obj.id)
    else:
        result["id"] = feature_obj.id

    return result


def assembly(assembly_obj: FeatureAssembly, json_format: bool = None):
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


def children(child_obj: Feature, json_format: bool = None):
    return {
        "ensembl_id": child_obj.ensembl_id,
        "assemblies": [assembly(a, json_format) for a in child_obj.assemblies.all()],
    }


def region(region_obj: DNARegion, json_format: bool = None):
    result = {
        "cell_line": region_obj.cell_line,
        "start": region_obj.location.lower,
        "end": region_obj.location.upper,
        "strand": region_obj.strand,
        "assembly": f"{region_obj.ref_genome}.{region_obj.ref_genome_patch or '0'}",
        "reg_effect_count": region_obj.regulatory_effects.count(),
    }

    if json_format == "genoverse":
        result["id"] = str(region_obj.id)
        result["chr"] = region_obj.chrom_name.removeprefix("chr")
    else:
        result["id"] = region_obj.id
        result["chr"] = region_obj.chrom_name

    return result


def reg_effect(re_obj: RegulatoryEffect, json_format=None):
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
