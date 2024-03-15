import csv

from utils.experiment import ExperimentMetadata

from .load_experiment import Experiment, FeatureRow
from .types import FeatureType, GenomeAssembly, RangeBounds


def get_features(experiment_metadata: ExperimentMetadata):
    feature_file = experiment_metadata.tested_elements_file
    feature_tsv = open(feature_file.filename, "r")
    reader = csv.DictReader(feature_tsv, delimiter=feature_file.delimiter(), quoting=csv.QUOTE_NONE)
    new_cars: dict[str, FeatureRow] = {}

    for line in reader:
        chrom_name = line["seqnames"]

        car_start = int(line["start"])
        car_end = int(line["end"])
        car_location = f"[{car_start},{car_end})"

        car_name = f"{chrom_name}:{car_location}"

        if car_name not in new_cars:
            new_cars[car_name] = FeatureRow(
                chrom_name=chrom_name,
                location=(car_start, car_end, RangeBounds.HALF_OPEN_RIGHT),
                genome_assembly=GenomeAssembly(feature_file.genome_assembly),
                cell_line=feature_file.biosample.cell_line,
                feature_type=FeatureType.CAR,
            )

    feature_tsv.close()
    return new_cars.values(), None


def run(experiment_filename):
    metadata = ExperimentMetadata.file_load(experiment_filename)
    Experiment(metadata).load(get_features).save()
