import csv

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    Analysis,
    DNAFeature,
    DNAFeatureType,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)
from utils import timer
from utils.experiment import AnalysisMetadata

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
    effects: list[RegulatoryEffectObservation],
    effect_directions: list[RegulatoryEffectObservation],
    targets: list[DNAFeature],
):
    with transaction.atomic():
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
def load_reg_effects(reo_file, accession_ids, analysis, ref_genome, ref_genome_patch, delimiter=","):
    experiment = analysis.experiment
    reader = csv.DictReader(reo_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources: list[DNAFeature] = []
    effects: list[RegulatoryEffectObservation] = []
    effect_directions: list[FacetValue] = []
    targets: list[DNAFeature] = []
    dhss = {}

    for line in reader:
        chrom_name = line["dhs_chrom"]

        dhs_start = int(line["dhs_start"])
        dhs_end = int(line["dhs_end"])
        dhs_string = f"{chrom_name}:{dhs_start}-{dhs_end}:{ref_genome}"

        if dhs_string in dhss:
            dhs = dhss[dhs_string]
        else:
            dhs_location = NumericRange(dhs_start, dhs_end, "[)")
            dhs = DNAFeature.objects.get(
                experiment_accession=experiment,
                chrom_name=chrom_name,
                location=dhs_location,
                ref_genome=ref_genome,
                feature_type=DNAFeatureType.DHS,
            )
            dhss[dhs_string] = dhs

        sources.append(dhs)

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
            target = DNAFeature.objects.get(
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
            target = DNAFeature.objects.get(
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                name=line["gene_symbol"],
                location=NumericRange(int(line["start"]), int(line["end"]), "[]"),
                ensembl_id__in=CORRECT_FEATURES,
            )

        effect = RegulatoryEffectObservation(
            accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
            experiment=experiment,
            experiment_accession=experiment,
            analysis=analysis,
            facet_num_values={
                RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: float(line["p_val"]),
                RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: significance,
            },
        )
        effects.append(effect)
        effect_directions.append(direction)
        targets.append(target)
    bulk_save(sources, effects, effect_directions, targets)


def unload_analysis(analysis_metadata):
    analysis = Analysis.objects.get(
        experiment_id=analysis_metadata.experiment_accession_id, name=analysis_metadata.name
    )
    RegulatoryEffectObservation.objects.filter(analysis=analysis).delete()
    analysis_metadata.db_del(analysis)


def check_filename(analysis_filename: str):
    if len(analysis_filename) == 0:
        raise ValueError(f"scCERES analysis filename '{analysis_filename}' must not be blank")


def run(analysis_filename):
    with open(analysis_filename) as analysis_file:
        analysis_metadata = AnalysisMetadata.json_load(analysis_file)
    check_filename(analysis_metadata.name)

    # Only run unload_analysis if you want to delete the analysis, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_analysis() uncommented is not, strictly, idempotent.
    # unload_analysis(analysis_metadata)

    analysis = analysis_metadata.db_save()

    with AccessionIds(message=f"{analysis.accession_id}: {analysis.name}"[:200]) as accession_ids:
        for reo_file, file_info, delimiter in analysis_metadata.metadata():
            load_reg_effects(
                reo_file,
                accession_ids,
                analysis,
                file_info.ref_genome,
                file_info.ref_genome_patch,
                delimiter,
            )
