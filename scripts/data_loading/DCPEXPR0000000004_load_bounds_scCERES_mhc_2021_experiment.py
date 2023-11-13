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

GRNA_TYPE_FACET = Facet.objects.get(name="gRNA Type")
GRNA_TYPE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_TYPE_FACET.id).all()}
GRNA_TYPE_POS_CTRL = GRNA_TYPE_FACET_VALUES["Positive Control"]
GRNA_TYPE_TARGETING = GRNA_TYPE_FACET_VALUES["Targeting"]

PROMOTER_FACET = Facet.objects.get(name="Promoter Classification")
PROMOTER_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=PROMOTER_FACET.id).all()}
PROMOTER_PROMOTER = PROMOTER_FACET_VALUES["Promoter"]
PROMOTER_NON_PROMOTER = PROMOTER_FACET_VALUES["Non-promoter"]


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
def bulk_save(grnas, grna_type_facets, grna_promoter_facets):
    with transaction.atomic():
        print("Adding gRNA Regions")
        DNAFeature.objects.bulk_create(grnas, batch_size=1000)

        for grna, type_facet, promoter_facet in zip(grnas, grna_type_facets, grna_promoter_facets):
            grna.facet_values.add(type_facet)
            grna.facet_values.add(promoter_facet)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load gRNAs")
def load_grnas(grna_file, accession_ids, experiment, region_source, cell_line, ref_genome, delimiter=","):
    reader = csv.DictReader(grna_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    grnas = {}
    grna_type_facets = []
    grna_promoter_facets = []
    for i, line in enumerate(reader):
        # every other line in this file is basically a duplicate of the previous line
        if i % 2 == 0:
            continue
        grna_id = line["grna"]
        grna_type = line["type"]
        grna_promoter_class = line["annotation_manual"]

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
                grna_type_facets.append(GRNA_TYPE_TARGETING)
            elif grna_type.startswith("positive_control") == "":
                grna_type_facets.append(GRNA_TYPE_POS_CTRL)

            if grna_promoter_class == "promoter":
                grna_promoter_facets.append(PROMOTER_PROMOTER)
            else:
                grna_promoter_facets.append(PROMOTER_NON_PROMOTER)

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
            guide = DNAFeature(
                accession_id=accession_ids.incr(AccessionType.GRNA),
                experiment_accession=experiment,
                source_file=region_source,
                cell_line=cell_line,
                chrom_name=chrom_name,
                location=grna_location,
                strand=strand,
                closest_gene=closest_gene,
                closest_gene_distance=distance,
                closest_gene_name=gene_name,
                closest_gene_ensembl_id=closest_gene.ensembl_id if closest_gene is not None else None,
                misc={"grna": grna_id},
                ref_genome=ref_genome,
                feature_type=DNAFeatureType.GRNA,
            )
            grnas[grna_id] = guide

    bulk_save(grnas.values(), grna_type_facets, grna_promoter_facets)


def unload_experiment(experiment_metadata):
    try:
        print(experiment_metadata.accession_id)
        experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    except Experiment.DoesNotExist:
        return
    except Exception as e:
        raise e

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
        for grna_file, file_info, delimiter in experiment_metadata.metadata():
            load_grnas(
                grna_file,
                accession_ids,
                experiment,
                experiment.files.all()[0],
                experiment_metadata.biosamples[0].cell_line,
                file_info.misc["ref_genome"],
                delimiter,
            )
