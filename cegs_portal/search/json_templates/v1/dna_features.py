from typing import Iterable, Optional, TypedDict, Union, cast

from cegs_portal.search.models import DNAFeature

FeatureJson = TypedDict(
    "FeatureJson",
    {
        "id": Union[int, str],
        "ensembl_id": str,
        "cell_line": str,
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
        "closest_gene_ensembl_id": Optional[int],
        "closest_gene_name": str,
    },
)


def features(feature_objs: Iterable[DNAFeature], json_format: str = None) -> list[FeatureJson]:
    return [feature(a, json_format) for a in feature_objs]


def feature(feature_obj: DNAFeature, json_format: str = None) -> FeatureJson:
    result = {
        "ensembl_id": feature_obj.ensembl_id,
        "closest_gene_ensembl_id": None,
        "cell_line": feature_obj.cell_line,
        "type": feature_obj.feature_type,
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.id if feature_obj.parent is not None else None,
        "name": feature_obj.name,
        "start": feature_obj.location.lower,
        "end": feature_obj.location.upper - 1,
        "strand": feature_obj.strand,
        "ids": feature_obj.ids,
        "misc": feature_obj.misc,
        "ref_genome": feature_obj.ref_genome,
        "ref_genome_patch": feature_obj.ref_genome_patch,
    }

    if feature_obj.closest_gene is not None:
        result["closest_gene_ensembl_id"] = feature_obj.closest_gene.ensembl_id

    if json_format == "genoverse":
        result["id"] = str(feature_obj.id)
        result["chr"] = feature_obj.chrom_name.removeprefix("chr")
    else:
        result["id"] = feature_obj.id
        result["chr"] = feature_obj.chrom_name

    return cast(FeatureJson, result)
