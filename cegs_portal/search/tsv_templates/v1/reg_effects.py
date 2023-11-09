from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.templatetags.custom_helpers import format_float, if_strand


def tested_element(source, target):
    return f"{source.chrom_name}:{source.location.lower}-{source.location.upper}:{if_strand(source.strand)}:{target.name if target else 'N/A'}"


def bed6_output(reos):
    tsv_data = []
    for reo in reos:
        sources = reo.sources.all()
        targets = reo.targets.all()

        if not targets:
            targets = [None]

        for target in targets:
            for source in sources:
                row = [
                    source.chrom_name,
                    source.location.lower,
                    source.location.upper,
                    tested_element(source, target) if target else "N/A",
                    "0",
                    if_strand(source.strand),
                ]

                tsv_data.append(row)

    return tsv_data


def reg_effects(reos, options):
    if is_bed6(options):
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
        sources = reo.sources.all()
        targets = reo.targets.all()

        if not targets:
            targets = [None]

        for target in targets:
            for source in sources:
                row = [
                    source.chrom_name,
                    source.location.lower,
                    source.location.upper,
                    tested_element(source, target) if target else "N/A",
                    "0",
                    if_strand(source.strand),
                    reo.effect_size,
                    reo.direction,
                    format_float(reo.significance),
                    reo.experiment.name,
                    target.name if target else "N/A",
                ]

                tsv_data.append(row)

    return tsv_data


def target_reg_effects(reos, options):
    if is_bed6(options):
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
        sources = reo.sources.all()
        targets = reo.targets.all()

        if not targets:
            targets = [None]

        for source in sources:
            for target in targets:
                row = [
                    source.chrom_name,
                    source.location.lower,
                    source.location.upper,
                    tested_element(source, target) if target else "N/A",
                    "0",
                    if_strand(source.strand),
                    reo.effect_size,
                    reo.direction,
                    format_float(reo.significance),
                    reo.experiment.name,
                ]

                tsv_data.append(row)

    return tsv_data
