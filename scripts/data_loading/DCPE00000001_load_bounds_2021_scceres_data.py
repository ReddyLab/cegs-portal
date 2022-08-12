import csv

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNAFeature,
    DNAFeatureType,
    Experiment,
    Facet,
    FacetValue,
    RegulatoryEffect,
)
from utils import ExperimentMetadata, timer

from . import get_closest_gene

DIR_FACET = Facet.objects.get(name="Direction")
DIR_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=DIR_FACET.id).all()}


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
def bulk_save(grnas, effects, effect_directions, sources, targets):
    with transaction.atomic():
        print("Adding gRNA Regions")
        DNAFeature.objects.bulk_create(grnas, batch_size=1000)

        print("Adding RegulatoryEffects")
        RegulatoryEffect.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding effect directions to effects")
        for direction, effect in zip(effect_directions, effects):
            effect.facet_values.add(direction)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffects")
        for source, effect in zip(sources, effects):
            effect.sources.add(source)
        print("Adding targets to RegulatoryEffects")
        for target, effect in zip(targets, effects):
            effect.targets.add(target)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, experiment, region_source, cell_line, ref_genome, ref_genome_patch, delimiter=","):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sites = []
    effects = []
    effect_directions = []
    target_assembiles = []
    grnas = {}
    for line in reader:
        grna = line["grna"]
        if grna in grnas:
            region = grnas[grna]
        else:
            grna_info = grna.split("-")

            if not grna_info[0].startswith("chr"):
                continue

            if len(grna_info) == 5:
                chrom_name, grna_start_str, grna_end_str, strand, _grna_seq = grna_info
            elif len(grna_info) == 6:
                chrom_name, grna_start_str, grna_end_str, _x, _y, _grna_seq = grna_info
                strand = "-"

            grna_start = int(grna_start_str)
            grna_end = int(grna_end_str)
            grna_location = NumericRange(grna_start, grna_end, "[]")

            closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, grna_start, grna_end)

            region = DNAFeature(
                cell_line=cell_line,
                chrom_name=chrom_name,
                closest_gene=closest_gene,
                closest_gene_distance=distance,
                closest_gene_name=gene_name,
                location=grna_location,
                misc={"grna": grna},
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                feature_type=DNAFeatureType.GRNA,
                source=region_source,
                strand=strand,
            )
            grnas[grna] = region
        sites.append(region)

        significance = float(line["pval_fdr_corrected"])
        effect_size = float(line["avg_logFC"])
        if significance >= 0.01:
            direction = DIR_FACET_VALUES["Non-significant"]
        elif effect_size > 0:
            direction = DIR_FACET_VALUES["Enriched Only"]
        elif effect_size < 0:
            direction = DIR_FACET_VALUES["Depleted Only"]
        else:
            direction = DIR_FACET_VALUES["Non-significant"]

        target_assembly = DNAFeature.objects.get(
            ref_genome=ref_genome, ref_genome_patch=ref_genome_patch, name=line["gene_symbol"]
        )

        effect = RegulatoryEffect(
            experiment=experiment,
            facet_num_values={
                RegulatoryEffect.Facet.EFFECT_SIZE.value: effect_size,
                RegulatoryEffect.Facet.RAW_P_VALUE.value: float(line["p_val"]),
                RegulatoryEffect.Facet.SIGNIFICANCE.value: significance,
            },
        )
        target_assembiles.append(target_assembly)
        effects.append(effect)
        effect_directions.append(direction)
    bulk_save(grnas.values(), effects, effect_directions, sites, target_assembiles)


def unload_reg_effects(experiment_metadata):
    experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    RegulatoryEffect.objects.filter(experiment=experiment).delete()
    for file in experiment.other_files.all():
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

    for i, meta in enumerate(experiment_metadata.metadata()):
        ceres_file, file_info, delimiter = meta
        load_reg_effects(
            ceres_file,
            experiment,
            experiment.other_files.all()[i],
            file_info.cell_line,
            file_info.ref_genome,
            file_info.ref_genome_patch,
            delimiter,
        )
