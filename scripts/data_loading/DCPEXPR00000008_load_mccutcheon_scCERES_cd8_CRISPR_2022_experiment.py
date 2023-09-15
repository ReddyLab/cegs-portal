import csv

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    Experiment,
    Facet,
    FacetValue,
)
from utils import ExperimentMetadata, timer

from . import get_closest_gene

# These gene names appear in the data and have a "version" ("".1") in a few instances.
# We don't know why. It's safe to remove the version for processing though.
TRIM_GENE_NAMES = [
    "HSPA14.1",
    "MATR3.1",
    "GGT1.1",
    "TMSB15B.1",
    "TBCE.1",
    "CYB561D2.1",
    "GOLGA8M.1",
    "LINC01238.1",
    "ARMCX5-GPRASP2.1",
    "LINC01505.1",
]

GRNA_TYPE_FACET = Facet.objects.get(name="gRNA Type")
GRNA_TYPE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_TYPE_FACET.id).all()}
GRNA_TYPE_TARGETING = GRNA_TYPE_FACET_VALUES["Targeting"]


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

        for grna in grnas:
            grna.facet_values.add(GRNA_TYPE_TARGETING)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load GRNAs")
def load_grnas(
    ceres_file,
    accession_ids,
    experiment,
    region_source,
    cell_line,
    ref_genome,
    delimiter=",",
):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    grnas = {}
    existing_grna_facets = {}
    for line in reader:
        target_gene = line["target_gene"]

        if target_gene in TRIM_GENE_NAMES:
            target_gene = target_gene[:-2]

        grna_id = line["grna"]
        if grna_id in grnas:
            guide = grnas[grna_id]
        else:
            existing_grna_facets[grna_id] = set()
            strand = line["Strand"]
            chrom_name = line["chr"]
            grna_start = int(line["start"])
            grna_end = int(line["end"])

            if strand == "+":
                bounds = "[)"
            elif strand == "-":
                bounds = "(]"

            grna_location = NumericRange(grna_start, grna_end, bounds)

            closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, grna_start, grna_end)

            guide = DNAFeature(
                accession_id=accession_ids.incr(AccessionType.GRNA),
                experiment_accession=experiment,
                source_file=region_source,
                cell_line=cell_line,
                chrom_name=chrom_name,
                closest_gene=closest_gene,
                closest_gene_distance=distance,
                closest_gene_name=gene_name,
                closest_gene_ensembl_id=closest_gene.ensembl_id if closest_gene is not None else None,
                location=grna_location,
                strand=strand,
                misc={"grna": grna_id},
                ref_genome=ref_genome,
                feature_type=DNAFeatureType.GRNA,
            )
            grnas[grna_id] = guide

    bulk_save(grnas.values())


def unload_experiment(experiment_metadata):
    experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    DNAFeature.objects.filter(experiment_accession=experiment).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"scCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename):
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
        ceres_file, file_info, _delimiter = next(experiment_metadata.metadata())
        load_grnas(
            ceres_file,
            accession_ids,
            experiment,
            experiment.files.all()[0],
            experiment_metadata.biosamples[0].cell_line,
            file_info.misc["ref_genome"],
            "\t",
        )
