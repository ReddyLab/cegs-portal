from cegs_portal.search.models import DNAFeature, RegulatoryEffect


def features(feature_objs: DNAFeature, json_format: str = None):
    results = [feature(f, json_format=json_format) for f in feature_objs]
    return results


def feature(feature_obj: DNAFeature, json_format: str = None):
    result = {
        "ensembl_id": feature_obj.ensembl_id,
        "cell_line": feature_obj.cell_line,
        "chr": feature_obj.chrom_name,
        "name": feature_obj.name,
        "start": feature_obj.location.lower,
        "end": feature_obj.location.upper,
        "strand": feature_obj.strand,
        "closest_gene_ensembl_id": None,
        "closest_gene_name": feature_obj.closest_gene_name,
        "assembly": f"{feature_obj.ref_genome}.{feature_obj.ref_genome_patch or '0'}",
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.ensembl_id if feature_obj.parent is not None else None,
        "misc": feature_obj.misc,
        "ids": feature_obj.ids,
        "facets": [value.value for value in feature_obj.facet_values.all()],
        "children": [children(c, json_format) for c in feature_obj.children.all()],
        "closest_features": [region(d, json_format) for d in feature_obj.closest_features.all()],
        "reg_effect_source_for": [reg_effect(r, json_format) for r in feature_obj.source_for.all()],
        "reg_effect_target_of": [reg_effect(r, json_format) for r in feature_obj.target_of.all()],
    }

    if feature_obj.closest_gene is not None:
        result["closest_gene_ensembl_id"] = feature_obj.closest_gene.ensembl_id

    if json_format == "genoverse":
        result["id"] = str(feature_obj.id)
        result["chr"] = feature_obj.chrom_name.removeprefix("chr")
    else:
        result["id"] = feature_obj.id
        result["chr"] = feature_obj.chrom_name

    return result


def children(child_obj: DNAFeature, json_format: str = None):
    return {
        "ensembl_id": child_obj.ensembl_id,
        "features": [feature(a, json_format) for a in child_obj.assemblies.all()],
    }


def region(region_obj: DNAFeature, json_format: str = None):
    result = {
        "cell_line": region_obj.cell_line,
        "start": region_obj.location.lower,
        "end": region_obj.location.upper,
        "strand": region_obj.strand,
        "assembly": f"{region_obj.ref_genome}.{region_obj.ref_genome_patch or '0'}",
        "reg_effect_count": region_obj.source_for.count() + region_obj.target_of.count(),
    }

    if json_format == "genoverse":
        result["id"] = str(region_obj.id)
        result["chr"] = region_obj.chrom_name.removeprefix("chr")
    else:
        result["id"] = region_obj.id
        result["chr"] = region_obj.chrom_name

    return result


def reg_effect(re_obj: RegulatoryEffect, json_format: str = None):
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

    return result
