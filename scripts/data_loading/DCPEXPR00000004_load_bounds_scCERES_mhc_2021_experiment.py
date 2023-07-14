import csv

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
def bulk_save(grnas):
    with transaction.atomic():
        print("Adding gRNA Regions")
        DNAFeature.objects.bulk_create(grnas, batch_size=1000)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load gRNAs")
def load_grnas(
    grna_file, accession_ids, experiment, region_source, cell_line, ref_genome, ref_genome_patch, delimiter=","
):
    reader = csv.DictReader(grna_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    grnas = {}
    grnas_to_save = []
    for i, line in enumerate(reader):
        # every other line in this file is basically a duplicate of the previous line
        if i % 2 == 0:
            continue
        grna_id = line["grna"]
        grna_type = line["type"]

        if grna_id in grnas:
            guide = grnas[grna_id]
        else:
            grna_info = grna_id.split("-")

            # Skip non-targeting guides
            if not grna_info[0].startswith("chr"):
                continue

            if len(grna_info) == 5:
                chrom_name, grna_start_str, grna_end_str, strand, _grna_seq = grna_info
            elif len(grna_info) == 6:
                chrom_name, grna_start_str, grna_end_str, _x, _y, _grna_seq = grna_info
                strand = "-"

            if strand == "+":
                bounds = "[)"
            elif strand == "-":
                bounds = "(]"

            if grna_type == "targeting":
                grna_start = int(grna_start_str)
                grna_end = int(grna_end_str)
            else:
                if strand == "+":
                    grna_start = int(grna_start_str)
                    grna_end = int(grna_start_str) + 20
                elif strand == "-":
                    grna_start = int(grna_end_str) - 20
                    grna_end = int(grna_end_str)
            grna_location = NumericRange(grna_start, grna_end, bounds)

            closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, grna_start, grna_end)

            try:
                guide = DNAFeature.objects.get(
                    chrom_name=chrom_name,
                    location=grna_location,
                    strand=strand,
                    ref_genome=ref_genome,
                    feature_type=DNAFeatureType.GRNA,
                )
            except DNAFeature.DoesNotExist:
                guide = DNAFeature(
                    accession_id=accession_ids.incr(AccessionType.GRNA),
                    experiment_accession_id=experiment.accession_id,
                    cell_line=cell_line,
                    chrom_name=chrom_name,
                    closest_gene=closest_gene,
                    closest_gene_distance=distance,
                    closest_gene_name=gene_name,
                    closest_gene_ensembl_id=closest_gene.ensembl_id,
                    location=grna_location,
                    misc={"grna": grna_id},
                    ref_genome=ref_genome,
                    ref_genome_patch=ref_genome_patch,
                    feature_type=DNAFeatureType.GRNA,
                    source=region_source,
                    strand=strand,
                )
                grnas_to_save.append(guide)
            except DNAFeature.MultipleObjectsReturned as e:
                guides = DNAFeature.objects.filter(
                    chrom_name=chrom_name,
                    location=grna_location,
                    ref_genome=ref_genome,
                    strand=strand,
                    feature_type=DNAFeatureType.GRNA,
                )
                print(f"{chrom_name}: {grna_location}, {grna_id}")
                for guide in guides.all():
                    print(guide.misc)
                raise e
            grnas[grna_id] = guide
    bulk_save(grnas_to_save)


def unload_reg_effects(experiment_metadata):
    try:
        print(experiment_metadata.accession_id)
        experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    except Experiment.DoesNotExist:
        return
    except Exception as e:
        raise e

    for file in experiment.files.all():
        DNAFeature.objects.filter(source=file).delete()
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
        for grna_file, file_info, delimiter in experiment_metadata.metadata():
            load_grnas(
                grna_file,
                accession_ids,
                experiment,
                experiment.files.all()[0],
                experiment_metadata.biosamples[0].cell_line,
                file_info.misc["ref_genome"],
                file_info.misc["ref_genome_patch"],
                delimiter,
            )
