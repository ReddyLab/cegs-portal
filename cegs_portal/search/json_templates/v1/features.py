from cegs_portal.search.models import Feature, FeatureAssembly


def features(feature_obj: dict[Feature, list[FeatureAssembly]], json_format: bool = None):
    feature_dict = [
        {
            "feature": feature(f, json_format),
            "assemblies": [assembly(a, json_format) for a in assemblies],
        }
        for f, assemblies in feature_obj.items()
    ]

    return feature_dict


def feature(feature_obj: Feature, json_format: bool = None):
    result = {
        "ensembl_id": feature_obj.ensembl_id,
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.id if feature_obj.parent is not None else None,
    }

    if json_format == "genoverse":
        result["id"] = str(feature_obj.id)
    else:
        result["id"] = feature_obj.id

    return result


def assembly(feature_assembly: FeatureAssembly, json_format: bool = None):
    result = {
        "name": feature_assembly.name,
        "start": feature_assembly.location.lower,
        "end": feature_assembly.location.upper - 1,
        "strand": feature_assembly.strand,
        "ids": feature_assembly.ids,
        "ref_genome": feature_assembly.ref_genome,
        "ref_genome_patch": feature_assembly.ref_genome_patch,
    }

    if json_format == "genoverse":
        result["id"] = str(feature_assembly.id)
        result["chr"] = feature_assembly.chrom_name.removeprefix("chr")
    else:
        result["id"] = feature_assembly.id
        result["chr"] = feature_assembly.chrom_name

    return result
