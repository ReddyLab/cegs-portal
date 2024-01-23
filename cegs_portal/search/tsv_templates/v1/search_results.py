from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.templatetags.custom_helpers import if_strand


def item_name(source, target):
    return f"{source.chrom_name}:{source.location.lower}-{source.location.upper}:{if_strand(source.strand)}:{f'{target.name}' if target is not None else ''}"


def sig_reos_bed6(reos):
    tsv_data = []
    for reo in reos:
        targets = list(reo.targets.all())
        targets = targets if len(targets) > 0 else [None]
        for target in targets:
            for source in reo.sources.all():
                row = [
                    source.chrom_name,
                    source.location.lower,
                    source.location.upper,
                    item_name(source, target),
                    "0",
                    if_strand(source.strand),
                ]

                tsv_data.append(row)

    return tsv_data


def sig_reos(data, options):
    reos = data
    if is_bed6(options):
        return sig_reos_bed6(reos)
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
        targets = list(reo.targets.all())
        targets = targets if len(targets) > 0 else [None]
        for target in targets:
            for source in reo.sources.all():
                row = [
                    source.chrom_name,
                    source.location.lower,
                    source.location.upper,
                    item_name(source, target),
                    "0",
                    if_strand(source.strand),
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
