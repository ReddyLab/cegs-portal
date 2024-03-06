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
        chrom_name = line["chrom"]
        dhs_start = int(line["chromStart"])
        dhs_end = int(line["chromEnd"])

        sources = [SourceInfo(chrom_name, dhs_start, dhs_end, "[)", None, FeatureType.DHS)]

        effect_size_field = line["wgCERES_score_top3_wg"].strip()
        if effect_size_field == "":
            effect_size = None
        else:
            effect_size = float(effect_size_field)

        direction_line = line["direction_wg"]
        if direction_line == "non_sig":
            direction = DirectionFacets.NON_SIGNIFICANT
        elif direction_line == "enriched":
            direction = DirectionFacets.ENRICHED
        elif direction_line == "depleted":
            direction = DirectionFacets.DEPLETED
        elif direction_line == "both":
            direction = DirectionFacets.BOTH
        else:
            direction = None

        facet_num_values = {
            NumericFacets.EFFECT_SIZE: effect_size,
            # line[pValue] is -log10(actual p-value), so raw_p_value uses the inverse operation
            NumericFacets.RAW_P_VALUE: pow(10, -float(line["pValue"])),
            # line[pValue] is -log10(actual p-value), but we want significance between 0 and 1
            # we perform the inverse operation.
            NumericFacets.SIGNIFICANCE: pow(10, -float(line["pValue"])),
            NumericFacets.LOG_SIGNIFICANCE: float(line["pValue"]),
        }

        observations.append(ObservationRow(sources, [], [direction], facet_num_values))

    return observations


def run(analysis_filename):
    metadata = AnalysisMetadata.file_load(analysis_filename)
    Analysis(metadata).load(get_observations).save()
