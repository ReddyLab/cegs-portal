import csv

from utils.experiment import AnalysisMetadata

from .DCPEXPR0000000004_utils import grna_loc
from .load_analysis import Analysis, ObservationRow, SourceInfo
from .types import DirectionFacets, FeatureType, NumericFacets


def get_observations(analysis_metadata: AnalysisMetadata):
    results_file = open(analysis_metadata.results.file_metadata.filename)
    reader = csv.DictReader(
        results_file, delimiter=analysis_metadata.results.file_metadata.delimiter(), quoting=csv.QUOTE_NONE
    )
    observations: list[ObservationRow] = []
    for i, line in enumerate(reader):
        # every other line in this file is basically a duplicate of the previous line
        if i % 2 == 0:
            continue

        grna_label = line["grna"]
        grna_info = grna_label.split("-")

        # Skip non-targeting guides and guides with no assigned enhancer
        if not grna_info[0].startswith("chr") or line["dhs.chr"] == "NA":
            continue

        chrom_name, grna_start, grna_end, grna_bounds, grna_strand = grna_loc(line)

        sources = [SourceInfo(chrom_name, grna_start, grna_end, grna_bounds, grna_strand, FeatureType.GRNA)]

        targets = [line["gene_stable_id"]]

        significance = float(line["pval_fdr_corrected"])
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
