from typing import Any, Iterable, Optional, TypedDict, Union, cast

from cegs_portal.search.json_templates import genoversify
from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import Pageable, PageableJson

FeatureJson = TypedDict(
    "FeatureJson",
    {
        "accession_id": str,
        "ensembl_id": str,
        "cell_line": str,
        "type": str,
        "subtype": str,
        "parent_id": Optional[str],
        "parent": str,
        "chr": str,
        "name": str,
        "start": int,
        "end": int,
        "strand": str,
        "ids": list[str],
        "ref_genome": str,
        "closest_gene_ensembl_id": Optional[int],
        "closest_gene_name": str,
    },
)


def features(
    feature_objs: Pageable[DNAFeature] | Iterable[DNAFeature], options: Optional[dict[str, Any]] = None
) -> Union[PageableJson, list[FeatureJson]]:
    if options is not None and options.get("paginate", False):
        feature_objs = cast(Pageable[DNAFeature], feature_objs)
        return {
            "object_list": [feature(a, options) for a in feature_objs.object_list],
            "page": feature_objs.number,
            "has_next_page": feature_objs.has_next(),
            "has_prev_page": feature_objs.has_previous(),
            "num_pages": feature_objs.paginator.num_pages,
        }
    else:
        cast(Iterable[DNAFeature], feature_objs)
        return [feature(a, options) for a in feature_objs]


def feature(feature_obj: DNAFeature, options: Optional[dict[str, Any]] = None) -> FeatureJson:
    result = {
        "accession_id": feature_obj.accession_id,
        "chr": feature_obj.chrom_name,
        "start": feature_obj.location.lower,
        "end": feature_obj.location.upper - 1,
        "strand": feature_obj.strand,
        "ensembl_id": feature_obj.ensembl_id,
        "closest_gene_name": feature_obj.closest_gene_name,
        "closest_gene_ensembl_id": feature_obj.closest_gene_ensembl_id,
        "cell_line": feature_obj.cell_line,
        "type": feature_obj.get_feature_type_display(),
        "subtype": feature_obj.feature_subtype,
        "parent_accession_id": feature_obj.parent_accession_id,
        "parent_ensembl_id": feature_obj.parent.ensembl_id if feature_obj.parent else None,
        "parent": feature_obj.parent.name if feature_obj.parent else None,
        "name": feature_obj.name,
        "ids": feature_obj.ids,
        "misc": feature_obj.misc,
        "ref_genome": feature_obj.ref_genome,
    }

    if options is not None:
        if "regeffects" in options.get("feature_properties", []):
            result["source_for"] = [reg_effect(r, options) for r in feature_obj.source_for.all()]
            result["target_of"] = [reg_effect(r, options) for r in feature_obj.target_of.all()]

        if "effect_directions" in options.get("feature_properties", []):
            result["effect_directions"] = feature_obj.effect_directions

        if "effect_targets" in options.get("feature_properties", []):
            result["effect_targets"] = feature_obj.effect_targets

        if options.get("json_format", None) == "genoverse":
            genoversify(result)

        if "screen_ccre" in options.get("feature_properties", []):
            result["ccre_type"] = feature_obj.ccre_type
    result["parent_subtype"] = feature_obj.parent.feature_subtype if feature_obj.parent else None

    return cast(FeatureJson, result)


def reg_effect(re_obj: RegulatoryEffectObservation, options: Optional[dict[str, Any]] = None):
    result = {
        "accession_id": re_obj.accession_id,
        "effect_size": re_obj.effect_size,
        "direction": re_obj.direction,
        "significance": re_obj.significance,
        "experiment_id": re_obj.experiment_accession_id,
        "sources": [{"name": feature.name, "ensembl_id": feature.ensembl_id} for feature in re_obj.sources.all()],
        "targets": [{"name": feature.name, "ensembl_id": feature.ensembl_id} for feature in re_obj.targets.all()],
    }

    if options is not None and options.get("json_format", None) == "genoverse":
        genoversify(result)

    return result
