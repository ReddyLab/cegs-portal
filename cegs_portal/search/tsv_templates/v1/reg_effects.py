from cegs_portal.search.templatetags.custom_helpers import format_float, if_strand


def tested_element(source):
    return f"{source.chrom_name}:{source.location.lower}-{source.location.upper}:{if_strand(source.strand)}:{source.get_feature_type_display()}"


def reg_effects(get_data, options):
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
            "Effect Size (log2FC)",
            "Direction",
            "Significance",
            "Experiment",
            "Target",
        ]
    )

    for reo in reg_effects_page:
        source = reo.sources.all()[0]
        row = [
            source.chrom_name,
            source.location.lower,
            source.location.upper,
            tested_element(source),
            "0",
            if_strand(source.strand),
            reo.effect_size,
            reo.direction,
            format_float(reo.significance),
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
            tested_element(source),
            "0",
            if_strand(source.strand),
            reo.effect_size,
            reo.direction,
            format_float(reo.significance),
            reo.experiment.name,
        ]

        tsv_data.append(row)

    return tsv_data
