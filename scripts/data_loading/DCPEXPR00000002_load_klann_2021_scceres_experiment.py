import csv

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    Experiment,
)
from utils import ExperimentMetadata, timer

from . import get_closest_gene

CORRECT_FEATURES = ["ENSG00000272333"]


#
# The following lines should work as expected when using postgres. See
# https://docs.djangoproject.com/en/3.1/ref/models/querysets/#bulk-create
#
#     If the model’s primary key is an AutoField, the primary key attribute can
#     only be retrieved on certain databases (currently PostgreSQL and MariaDB 10.5+).
#     On other databases, it will not be set.
#
# So the objects won't need to be saved one-at-a-time like they are, which is slow.
#
# In postgres the objects automatically get their id's when bulk_created but
# objects that reference the bulk_created objects (i.e., with foreign keys) don't
# get their foreign keys updated. The for loops do that necessary updating.
def bulk_save(dhss: list[DNAFeature]):
    with transaction.atomic():
        print("Adding DNaseIHypersensitiveSites")
        DNAFeature.objects.bulk_create(dhss, batch_size=1000)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load DHSs")
def load_dhss(
    dhs_file, accession_ids, experiment, cell_line, ref_genome, ref_genome_patch, region_source, delimiter=","
):
    reader = csv.DictReader(dhs_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    new_dhss: list[DNAFeature] = []

    for line in reader:
        chrom_name = line["dhs_chrom"]

        dhs_start = int(line["dhs_start"])
        dhs_end = int(line["dhs_end"])
        dhs_location = NumericRange(dhs_start, dhs_end, "[]")

        try:
            dhs = DNAFeature.objects.get(
                chrom_name=chrom_name,
                location__overlap=dhs_location,
                ref_genome=ref_genome,
                feature_type=DNAFeatureType.DHS,
            )
        except ObjectDoesNotExist:
            closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, dhs_start, dhs_end)
            dhs = DNAFeature(
                accession_id=accession_ids.incr(AccessionType.DHS),
                experiment_accession_id=experiment.accession_id,
                source_file=region_source,
                cell_line=cell_line,
                chrom_name=chrom_name,
                closest_gene=closest_gene,
                closest_gene_distance=distance,
                closest_gene_name=gene_name,
                closest_gene_ensembl_id=closest_gene.ensembl_id,
                location=dhs_location,
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                feature_type=DNAFeatureType.DHS,
            )
            new_dhss.append(dhs)
    print(f"DHS Count: {len(new_dhss)}")
    bulk_save(new_dhss)


def unload_reg_effects(experiment_metadata):
    experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    for file in experiment.files.all():
        DNAFeature.objects.filter(source_file=file).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"scCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename):
    with open(experiment_filename) as experiment_file:
        experiment_metadata = ExperimentMetadata.json_load(experiment_file)
    check_filename(experiment_metadata.name)

    # Only run unload_reg_effects if you want to delete the experiment, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects(experiment_metadata)

    experiment = experiment_metadata.db_save()

    with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
        for dhs_file, file_info, delimiter in experiment_metadata.metadata():
            load_dhss(
                dhs_file,
                accession_ids,
                experiment,
                experiment_metadata.biosamples[0].cell_line,
                file_info.misc["ref_genome"],
                file_info.misc["ref_genome_patch"],
                experiment.files.all()[0],
                delimiter,
            )
