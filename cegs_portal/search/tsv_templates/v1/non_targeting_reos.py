from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.templatetags.custom_helpers import if_strand


def item_name(source, feature):
    return f"{source.chrom_name}:{source.location.lower}-{source.location.upper}:{if_strand(feature.strand)}:{feature.name}"


def bed6_output(reos, feature):
    tsv_data = []
    for reo in reos:
        for source in reo.sources.all():
            row = [
                source.chrom_name,
                source.location.lower,
                source.location.upper,
                item_name(source, feature),
                "0",
                if_strand(feature.strand),
            ]

            tsv_data.append(row)

    return tsv_data


def non_targeting_regulatory_effects(data, options):
    reos, feature = data
    if is_bed6(options):
        return bed6_output(reos, feature)
    tsv_data = []
    tsv_data.append(
        [
            "chrom",
            "chromStart",
            "chromEnd",
            "name",
            "score",
            "strand",
            "Effect Size",
            "Direction",
            "Significance",
            "Distance",
            "Feature Type",
            "Experiment",
            "Effect ID",
        ]
    )

    for reo in reos:
        for source in reo.sources.all():
            row = [
                source.chrom_name,
                source.location.lower,
                source.location.upper,
                item_name(source, feature),
                "0",
                if_strand(feature.strand),
                reo.effect_size,
                reo.direction,
                reo.significance,
                source.closest_gene_distance,
                source.get_feature_type_display(),
                reo.experiment.name,
                reo.accession_id,
            ]

            tsv_data.append(row)

    return tsv_data
