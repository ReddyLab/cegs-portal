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
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)
from utils import ExperimentMetadata, timer

from . import get_closest_gene

DIR_FACET = Facet.objects.get(name="Direction")
DIR_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=DIR_FACET.id).all()}


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
def bulk_save(
    sources: list[DNAFeature],
    dhss: list[DNAFeature],
    effects: list[RegulatoryEffectObservation],
    effect_directions: list[RegulatoryEffectObservation],
    targets: list[DNAFeature],
):
    with transaction.atomic():
        print("Adding DNaseIHypersensitiveSites")
        DNAFeature.objects.bulk_create(dhss, batch_size=1000)

        print("Adding RegulatoryEffectObservations")
        RegulatoryEffectObservation.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding effect directions to effects")
        for direction, effect in zip(effect_directions, effects):
            effect.facet_values.add(direction)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffectObservations")
        for source, effect in zip(sources, effects):
            effect.sources.add(source)
        print("Adding targets to RegulatoryEffectObservations")
        for assembly, effect in zip(targets, effects):
            effect.targets.add(assembly)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(
    ceres_file, accession_ids, experiment, cell_line, ref_genome, ref_genome_patch, region_source, delimiter=","
):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sites: list[DNAFeature] = []
    new_sites: list[DNAFeature] = []
    effects: list[RegulatoryEffectObservation] = []
    effect_directions: list[FacetValue] = []
    targets: list[DNAFeature] = []

    for line in reader:
        chrom_name = line["dhs_chrom"]

        dhs_start = int(line["dhs_start"])
        dhs_end = int(line["dhs_end"])
        dhs_location = NumericRange(dhs_start, dhs_end, "[]")

        try:
            dhs = DNAFeature.objects.get(chrom_name=chrom_name, location=dhs_location, ref_genome=ref_genome)
        except ObjectDoesNotExist:
            closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, dhs_start, dhs_end)
            dhs = DNAFeature(
                accession_id=accession_ids.incr(AccessionType.DHS),
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
                source=region_source,
            )
            new_sites.append(dhs)

        sites.append(dhs)

        significance = float(line["pval_empirical"])
        effect_size = float(line["avg_logFC"])
        if significance >= 0.01:
            direction = DIR_FACET_VALUES["Non-significant"]
        elif effect_size > 0:
            direction = DIR_FACET_VALUES["Enriched Only"]
        elif effect_size < 0:
            direction = DIR_FACET_VALUES["Depleted Only"]
        else:
            direction = DIR_FACET_VALUES["Non-significant"]

        try:
            target_assembly = DNAFeature.objects.get(
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                name=line["gene_symbol"],
                location=NumericRange(int(line["start"]), int(line["end"]), "[]"),
            )
        except DNAFeature.MultipleObjectsReturned:
            # There is ONE instance where there are two genes with the same name
            # in the exact same location. This handles that situation.
            # The two gene IDs are ENSG00000272333 and ENSG00000105663.
            # I decided that ENSG00000272333 was the "correct" gene to use here
            # because it's the one that still exists in GRCh38.
            target_assembly = DNAFeature.objects.get(
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                name=line["gene_symbol"],
                location=NumericRange(int(line["start"]), int(line["end"]), "[]"),
                ensembl_id__in=CORRECT_FEATURES,
            )

        effect = RegulatoryEffectObservation(
            accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
            experiment=experiment,
            experiment_accession_id=experiment.accession_id,
            facet_num_values={
                RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: float(line["p_val"]),
                RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: significance,
            },
        )
        targets.append(target_assembly)
        effects.append(effect)
        effect_directions.append(direction)
    print(f"New DHS Count: {len(new_sites)}")
    bulk_save(sites, new_sites, effects, effect_directions, targets)


def unload_reg_effects(experiment_metadata):
    experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    RegulatoryEffectObservation.objects.filter(experiment=experiment).delete()
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

    with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
        for ceres_file, file_info, delimiter in experiment_metadata.metadata():
            load_reg_effects(
                ceres_file,
                accession_ids,
                experiment,
                file_info.cell_line,
                file_info.ref_genome,
                file_info.ref_genome_patch,
                experiment.other_files.all()[0],
                delimiter,
            )
