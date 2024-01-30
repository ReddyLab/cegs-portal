from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.templatetags.custom_helpers import if_strand


def feature_name(feature):
    return f"{feature.chrom_name}:{feature.location.lower}-{feature.location.upper}:{if_strand(feature.strand)}:{f'{feature.name}' if feature is not None and feature.name is not None else ''}"


def dnafeatures_bed6(features):
    tsv_data = []
    for feature in features:
        row = [
            feature.chrom_name,
            feature.location.lower,
            feature.location.upper,
            feature_name(feature),
            "0",
            if_strand(feature.strand),
        ]

        tsv_data.append(row)

    return tsv_data


def dnafeatures(data, options):
    features, reo = data
    if is_bed6(options):
        return dnafeatures_bed6(features)
    tsv_data = []
    tsv_data.append(
        [
            "chrom",
            "chromStart",
            "chromEnd",
            "name",
            "score",
            "strand",
            "Distance",
            "Feature Type",
            "Accession ID",
            "Effect Size (log2FC)",
            "Direction",
            "Significance",
            "Experiment",
        ]
    )

    for feature in features:
        row = [
            feature.chrom_name,
            feature.location.lower,
            feature.location.upper,
            feature_name(feature),
            "0",
            if_strand(feature.strand),
            feature.closest_gene_distance,
            feature.get_feature_type_display(),
            feature.accession_id,
            reo.effect_size,
            reo.direction,
            reo.significance,
            feature.experiment_accession_id,
        ]

        tsv_data.append(row)

    return tsv_data
