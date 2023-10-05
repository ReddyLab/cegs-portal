def reg_effects(get_data):
    reg_effects_page = get_data
    tsv_data = []
    tsv_data.append(
        ["Accession ID", "Effect Size", "Direction", "Significance", "Distance", "Feature Type", "Source", "Experiment"]
    )

    for reo in reg_effects_page:
        first_source = reo.sources.all()[0]
        row = [
            reo.accession_id,
            reo.effect_size,
            reo.direction,
            reo.significance,
            first_source.closest_gene_distance,
            first_source.get_feature_type_display(),
            first_source.accession_id,
            reo.experiment.name,
        ]

        tsv_data.append(row)

    return tsv_data
