import csv

from utils.experiment import AnalysisMetadata

from .DCPEXPR0000000008_consts import DROP_GENE_NAMES, TRIM_GENE_NAMES
from .load_analysis import Analysis, ObservationRow, SourceInfo


def gene_ensembl_mapping(features_file):
    gene_name_map = {}
    with open(features_file, newline="") as facet_file:
        reader = csv.reader(facet_file, delimiter="\t")
        for row in reader:
            if row[2] != "Gene Expression":
                continue
            gene_name_map[row[1]] = row[0]

    return gene_name_map


def get_observations(analysis_metadata: AnalysisMetadata):
    gene_name_map = gene_ensembl_mapping(analysis_metadata.misc_files[0].filename)
    results_file = open(analysis_metadata.results.file_metadata.filename)
    reader = csv.DictReader(
        results_file, delimiter=analysis_metadata.results.file_metadata.delimiter(), quoting=csv.QUOTE_NONE
    )
    observations: list[ObservationRow] = []
    for line in reader:
        target_gene = line["target_gene"]

        if target_gene in TRIM_GENE_NAMES:
            target_gene = target_gene[:-2]

        if gene_name_map[target_gene] in DROP_GENE_NAMES:
            continue

        strand = line["Strand"]
        chrom_name = line["chr"]
        grna_start = int(line["start"])
        grna_end = int(line["end"])

        if strand == "+":
            bounds = "[)"
        elif strand == "-":
            bounds = "(]"

        sources = [SourceInfo(chrom_name, grna_start, grna_end, bounds, "gRNA")]

        targets = [gene_name_map[target_gene]]

        significance = float(line["p_val_adj"])
        effect_size = float(line["avg_log2FC"])
        if significance >= 0.01:
            direction = "Non-significant"
        elif effect_size > 0:
            direction = "Enriched Only"
        elif effect_size < 0:
            direction = "Depleted Only"
        else:
            direction = "Non-significant"

        observations.append(
            ObservationRow(sources, targets, direction, effect_size, float(line["p_val"]), significance)
        )
    results_file.close()
    return observations


def run(analysis_filename):
    Analysis(analysis_filename).load(get_observations).save()
