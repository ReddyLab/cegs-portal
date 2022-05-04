from typing import Iterable, Optional, TypedDict, Union, cast

from cegs_portal.search.models import FeatureAssembly

AssemblyJson = TypedDict(
    "AssemblyJson",
    {
        "id": Union[int, str],
        "ensembl_id": str,
        "type": str,
        "subtype": str,
        "parent_id": Optional[str],
        "chr": str,
        "name": str,
        "start": int,
        "end": int,
        "strand": str,
        "ids": list[str],
        "ref_genome": str,
        "ref_genome_patch": str,
    },
)


def feature_assemblies(assembly_obj: Iterable[FeatureAssembly], json_format: str = None) -> list[AssemblyJson]:
    return [assembly(a, json_format) for a in assembly_obj]


def assembly(feature_assembly: FeatureAssembly, json_format: str = None) -> AssemblyJson:
    result = {
        "ensembl_id": feature_assembly.ensembl_id,
        "type": feature_assembly.feature_type,
        "subtype": feature_assembly.feature_subtype,
        "parent_id": feature_assembly.parent.id if feature_assembly.parent is not None else None,
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

    return cast(AssemblyJson, result)
