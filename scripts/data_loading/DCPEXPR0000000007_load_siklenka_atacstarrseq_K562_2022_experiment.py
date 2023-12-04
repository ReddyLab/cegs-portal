import csv
from io import StringIO
from os import SEEK_SET

from django.db import connection, transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    Experiment,
)
from utils import timer
from utils.ccres import CcreSource, associate_ccres
from utils.db_ids import FeatureIds
from utils.experiment import ExperimentMetadata

from . import get_closest_gene


def save_data(cars: StringIO):
    cars.seek(0, SEEK_SET)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.copy_from(
            cars,
            "search_dnafeature",
            columns=(
                "id",
                "accession_id",
                "cell_line",
                "chrom_name",
                "closest_gene_id",
                "closest_gene_distance",
                "closest_gene_name",
                "closest_gene_ensembl_id",
                "location",
                "ref_genome",
                "ref_genome_patch",
                "feature_type",
                "source_file_id",
                "experiment_accession_id",
                "archived",
                "public",
            ),
        )


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load CARs")
def load_cars(
    ceres_file, closest_ccre_filename, accession_ids, experiment, cell_line, ref_genome, region_source, delimiter=","
):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    new_cars: dict[str, CcreSource] = {}
    cars = StringIO()
    region_source_id = region_source.id
    experiment_accession_id = experiment.accession_id
    with FeatureIds() as feature_ids:
        for feature_id, line in zip(feature_ids, reader):
            chrom_name = line["seqnames"]

            car_start = int(line["start"])
            car_end = int(line["end"])
            car_location = f"[{car_start},{car_end})"

            car_name = f"{chrom_name}:{car_location}"

            if car_name not in new_cars:
                closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, car_start, car_end)
                closest_gene_ensembl_id = closest_gene["ensembl_id"] if closest_gene is not None else None

                cars.write(
                    f"{feature_id}\t{accession_ids.incr(AccessionType.CAR)}\t{cell_line}\t{chrom_name}\t{closest_gene['id']}\t{distance}\t{gene_name}\t{closest_gene_ensembl_id}\t{car_location}\t{ref_genome}\t0\t{DNAFeatureType.CAR}\t{region_source_id}\t{experiment_accession_id}\tfalse\ttrue\n"
                )
                new_cars[car_name] = CcreSource(
                    _id=feature_id,
                    chrom_name=chrom_name,
                    location=NumericRange(car_start, car_end),
                    cell_line=cell_line,
                    closest_gene_id=closest_gene["id"],
                    closest_gene_distance=distance,
                    closest_gene_name=gene_name,
                    closest_gene_ensembl_id=closest_gene_ensembl_id,
                    ref_genome=ref_genome,
                    source_file_id=region_source_id,
                    experiment_accession_id=experiment_accession_id,
                )
    save_data(cars)

    associate_ccres(closest_ccre_filename, new_cars.values(), ref_genome, accession_ids)


def unload_experiment(experiment_metadata):
    experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    DNAFeature.objects.filter(experiment_accession=experiment).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"wgCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename, closest_ccre_filename):
    with open(experiment_filename) as experiment_file:
        experiment_metadata = ExperimentMetadata.json_load(experiment_file)
    check_filename(experiment_metadata.name)

    # Only run unload_experiment if you want to delete the experiment, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_experiment() uncommented is not, strictly, idempotent.
    # unload_experiment(experiment_metadata)

    experiment = experiment_metadata.db_save()

    with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
        for ceres_file, file_info, _delimiter in experiment_metadata.metadata():
            load_cars(
                ceres_file,
                closest_ccre_filename,
                accession_ids,
                experiment,
                experiment_metadata.biosamples[0].cell_line,
                file_info.misc["ref_genome"],
                experiment.files.all()[0],
                "\t",
            )
