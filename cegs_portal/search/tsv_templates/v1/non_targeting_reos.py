from cegs_portal.search.templatetags.custom_helpers import format_float


def non_targeting_regulatory_effects(data):
    reos, feature = data
    tsv_data = []
    tsv_data.append(
        [
            "# chrom",
            "chromStart",
            "chromEnd",
            "name",
            "strand",
            "score",
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
                feature.name,
                feature.strand,
                ".",
                format_float(reo.effect_size),
                reo.direction,
                format_float(reo.significance),
                source.closest_gene_distance,
                source.get_feature_type_display(),
                reo.experiment.name,
                reo.accession_id,
            ]

        tsv_data.append(row)

    return tsv_data
