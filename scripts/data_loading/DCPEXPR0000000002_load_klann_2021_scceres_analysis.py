import csv

from utils.experiment import AnalysisMetadata

from .load_analysis import Analysis, ObservationRow, SourceInfo
from .types import DirectionFacets, FeatureType, NumericFacets


def gene_ensembl_mapping(genes_filename):
    gene_name_map = {}
    with open(genes_filename, newline="") as genes_file:
        reader = csv.reader(genes_file, delimiter="\t")
        for row in reader:
            gene_name_map[row[0]] = row[1]

    return gene_name_map


def get_observations(analysis_metadata: AnalysisMetadata):
    gene_name_map = gene_ensembl_mapping(analysis_metadata.misc_files[0].filename)
    results_file = open(analysis_metadata.results.file_metadata.filename)
    reader = csv.DictReader(
        results_file, delimiter=analysis_metadata.results.file_metadata.delimiter(), quoting=csv.QUOTE_NONE
    )
    observations: list[ObservationRow] = []

    for line in reader:
        chrom_name = line["dhs_chrom"]

        dhs_start = int(line["dhs_start"])
        dhs_end = int(line["dhs_end"])

        sources = [SourceInfo(chrom_name, dhs_start, dhs_end, "[)", None, FeatureType.DHS)]

        targets = [gene_name_map[line["gene_symbol"]]]

        significance = float(line["pval_empirical"])
        effect_size = float(line["avg_logFC"])
        if significance >= 0.01:
            direction = DirectionFacets.NON_SIGNIFICANT
        elif effect_size > 0:
            direction = DirectionFacets.ENRICHED
        elif effect_size < 0:
            direction = DirectionFacets.DEPLETED
        else:
            direction = DirectionFacets.NON_SIGNIFICANT

        num_facets = {
            NumericFacets.EFFECT_SIZE: effect_size,
            NumericFacets.SIGNIFICANCE: significance,
            NumericFacets.RAW_P_VALUE: float(line["p_val"]),
        }

        observations.append(ObservationRow(sources, targets, [direction], num_facets))

    results_file.close()
    return observations


def run(analysis_filename):
    metadata = AnalysisMetadata.file_load(analysis_filename)
    Analysis(metadata).load(get_observations).save()
