def non_targeting_regulatory_effects(data):
    reo_page, feature = data
    tsv_data = []
    tsv_data.append(
        [
            "chrom",
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
        ]
    )

    for reo in reo_page:
        first_source = reo.sources.all()[0]
        row = [
            first_source.chrom_name,
            first_source.location.lower,
            first_source.location.upper,
            feature.name,
            feature.strand,
            " ",
            reo.effect_size,
            reo.direction,
            reo.significance,
            first_source.closest_gene_distance,
            first_source.get_feature_type_display(),
            reo.experiment.name,
        ]

        tsv_data.append(row)

    return tsv_data
