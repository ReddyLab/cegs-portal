def if_strand(value):
    if value is not None:
        return value
    else:
        return "."


def tested_elements(source):
    return f"{source.get_feature_type_display()}{source.chrom_name}:{source.location.lower}-{source.location.upper}:{if_strand(source.strand)}:{source.name}"


def reg_effects(get_data, options):
    reg_effects_page = get_data
    tsv_data = []
    tsv_data.append(["Effect Size (log2FC)", "Direction", "Significance", "Experiment", "Target"])

    for reo in reg_effects_page:
        source = reo.sources.all()[0]
        row = [
            reo.effect_size,
            reo.direction,
            reo.significance,
            reo.experiment.name,
            source.closest_gene_distance,
        ]

        tsv_data.append(row)

    return tsv_data


def target_reg_effects(get_data, options):
    reg_effects_page = get_data
    tsv_data = []
    tsv_data.append(
        [
            "#chrom",
            "chromStart",
            "chromEnd",
            "name",
            "score",
            "strand",
            "Tested Elements",
            "Effect Size",
            "Direction",
            "Significance",
            "Experiment",
        ]
    )

    for reo in reg_effects_page:
        source = reo.sources.all()[0]
        row = [
            source.chrom_name,
            source.location.lower,
            source.location.upper,
            tested_elements(source),
            "0",
            if_strand(source.strand),
            reo.effect_size,
            reo.direction,
            reo.significance,
            reo.experiment.name,
        ]

        tsv_data.append(row)

    return tsv_data
