import csv

from utils.experiment import AnalysisMetadata

from .load_analysis import Analysis, ObservationRow, SourceInfo
from .types import DirectionFacets, FeatureType, NumericFacets


def get_observations(analysis_metadata: AnalysisMetadata):
    results_file = open(analysis_metadata.results.file_metadata.filename)
    reader = csv.DictReader(
        results_file, delimiter=analysis_metadata.results.file_metadata.delimiter(), quoting=csv.QUOTE_NONE
    )
    observations: list[ObservationRow] = []

    for line in reader:
        chrom_name = line["seqnames"]

        car_start = int(line["start"])
        car_end = int(line["end"])

        sources = [SourceInfo(chrom_name, car_start, car_end, "[)", None, FeatureType.CAR)]

        effect_size_field = line["logFC"].strip()
        if effect_size_field == "":
            effect_size = None
        else:
            effect_size = float(effect_size_field)

        log_significance = float(line["minusLog10PValue"])
        if log_significance < 2:  # p-value < 0.01, we're being stricter about significance with this data set
            direction = DirectionFacets.NON_SIGNIFICANT
        elif effect_size > 0:
            direction = DirectionFacets.ENRICHED
        elif effect_size < 0:
            direction = DirectionFacets.DEPLETED
        else:
            direction = None

        significance = pow(10, -float(log_significance))
        p_val = significance

        facet_num_values = {
            NumericFacets.EFFECT_SIZE: effect_size,
            # significance is -log10(actual significance), but we want significance between 0 and 1
            # we perform the inverse operation.
            NumericFacets.SIGNIFICANCE: significance,
            NumericFacets.LOG_SIGNIFICANCE: log_significance,
            # significance is -log10(actual p-value), so raw_p_value uses the inverse operation
            NumericFacets.RAW_P_VALUE: p_val,
            NumericFacets.AVG_COUNTS_PER_MILLION: float(line["input_avg_counts.cpm"]),
        }

        observations.append(ObservationRow(sources, [], [direction], facet_num_values))

    return observations


def run(analysis_filename):
    metadata = AnalysisMetadata.file_load(analysis_filename)
    Analysis(metadata).load(get_observations).save()
