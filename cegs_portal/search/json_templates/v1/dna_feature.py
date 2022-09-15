from typing import Any, Optional

from cegs_portal.search.json_templates import genoversify
from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation


def features(feature_objs: DNAFeature, options: Optional[dict[str, Any]] = None):
    return [feature(f, options=options) for f in feature_objs]


def feature(feature_obj: DNAFeature, options: Optional[dict[str, Any]] = None):
    result = {
        "id": feature_obj.id,
        "ensembl_id": feature_obj.ensembl_id,
        "cell_line": feature_obj.cell_line,
        "name": feature_obj.name,
        "chr": feature_obj.chrom_name,
        "start": feature_obj.location.lower,
        "end": feature_obj.location.upper,
        "strand": feature_obj.strand,
        "closest_gene_ensembl_id": feature_obj.closest_gene.ensembl_id
        if feature_obj.closest_gene is not None
        else None,
        "closest_gene_name": feature_obj.closest_gene_name,
        "assembly": f"{feature_obj.ref_genome}.{feature_obj.ref_genome_patch or '0'}",
        "type": feature_obj.get_feature_type_display(),
        "subtype": feature_obj.feature_subtype,
        "parent_id": feature_obj.parent.ensembl_id if feature_obj.parent is not None else None,
        "misc": feature_obj.misc,
        "ids": feature_obj.ids,
        "facets": [value.value for value in feature_obj.facet_values.all()],
        "children": [feature(c, options) for c in feature_obj.children.all()],
        "closest_features": [region(d, options) for d in feature_obj.closest_features.all()],
        "reg_effect_source_for": [reg_effect(r, options) for r in feature_obj.source_for.all()],
        "reg_effect_target_of": [reg_effect(r, options) for r in feature_obj.target_of.all()],
    }

    if options is not None and options.get("json_format", None) == "genoverse":
        genoversify(result)

    return result


def region(region_obj: DNAFeature, options: Optional[dict[str, Any]] = None):
    result = {
        "id": region_obj.id,
        "chr": region_obj.chrom_name,
        "cell_line": region_obj.cell_line,
        "start": region_obj.location.lower,
        "end": region_obj.location.upper,
        "strand": region_obj.strand,
        "assembly": f"{region_obj.ref_genome}.{region_obj.ref_genome_patch or '0'}",
        "reg_effect_count": region_obj.source_for.count() + region_obj.target_of.count(),
    }

    if options is not None and options.get("json_format", None) == "genoverse":
        genoversify(result)

    return result


def reg_effect(re_obj: RegulatoryEffectObservation, options: Optional[dict[str, Any]] = None):
    result = {
        "id": re_obj.id,
        "effect_size": re_obj.effect_size,
        "direction": re_obj.direction,
        "significance": re_obj.significance,
        "experiment_id": re_obj.experiment_id,
        "source_ids": [dhs.id for dhs in re_obj.sources.all()],
    }

    if options is not None and options.get("json_format", None) == "genoverse":
        genoversify(result)

    return result
