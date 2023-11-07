from cegs_portal.search.templatetags.custom_helpers import format_float, if_strand


def tested_element(source):
    return f"{source.chrom_name}:{source.location.lower}-{source.location.upper}:{if_strand(source.strand)}:{source.get_feature_type_display()}"


def bed6_output(reos):
    tsv_data = []
    for reo in reos:
        for source in reo.sources.all():
            row = [
                source.chrom_name,
                source.location.lower,
                source.location.upper,
                tested_element(source),
                "0",
                if_strand(source.strand),
            ]

            tsv_data.append(row)

    return tsv_data


def reg_effects(reos, options):
    if options is not None and options.get("tsv_format", None) == "bed6":
        return bed6_output(reos)
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

    for reo in reos:
        for source in reo.sources.all():
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


def target_reg_effects(reos, options):
    if options is not None and options.get("tsv_format", None) == "bed6":
        return bed6_output(reos)
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

    for reo in reos:
        for source in reo.sources.all():
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
