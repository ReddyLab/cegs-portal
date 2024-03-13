import csv

from utils.experiment import ExperimentMetadata

from .load_experiment import Experiment, FeatureRow
from .types import FeatureType


def get_features(experiment_metadata: ExperimentMetadata):
    new_dhss: dict[str, FeatureRow] = {}

    dhs_file = experiment_metadata.tested_elements_file
    dhs_cell_line = dhs_file.biosample.cell_line

    feature_tsv = open(dhs_file.filename, "r")
    reader = csv.DictReader(feature_tsv, delimiter=dhs_file.delimiter(), quoting=csv.QUOTE_NONE)

    for line in reader:
        chrom_name = line["chrom"]

        dhs_start = int(line["chromStart"])
        dhs_end = int(line["chromEnd"])
        dhs_location = f"[{dhs_start},{dhs_end})"

        dhs_name = f"{chrom_name}:{dhs_location}"

        if dhs_name not in new_dhss:
            new_dhss[dhs_name] = FeatureRow(
                name=dhs_name,
                chrom_name=chrom_name,
                location=(dhs_start, dhs_end, "[)"),
                genome_assembly=dhs_file.genome_assembly,
                cell_line=dhs_cell_line,
                feature_type=FeatureType.DHS,
            )

    feature_tsv.close()
    return new_dhss.values(), None


def run(experiment_filename):
    metadata = ExperimentMetadata.file_load(experiment_filename)
    Experiment(metadata).load(get_features).save()
