from typing import Iterable

from cegs_portal.search.models import Feature, FeatureAssembly


def feature_assemblies(assembly_obj: Iterable[FeatureAssembly], json_format: str = None):
    feature_dict = {}
    for a in assembly_obj:
        a_list = feature_dict.get(a.feature, [])
        a_list.append(a)
        feature_dict[a.feature] = a_list

    feature_dicts = [
        {
            "feature": feature(f, json_format),
            "assemblies": [assembly(a, json_format) for a in a_list],
        }
        for f, a_list in feature_dict.items()
    ]

    return feature_dicts


def features(feature_obj: Iterable[Feature], json_format: str = None):
    feature_dict = [
        {
            "feature": feature(f, json_format),
            "assemblies": [assembly(a, json_format) for a in f.assemblies.all()],
        }
        for f in feature_obj
    ]

    return feature_dict


def feature(feature_obj: Feature, json_format: str = None):
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


def assembly(feature_assembly: FeatureAssembly, json_format: str = None):
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
