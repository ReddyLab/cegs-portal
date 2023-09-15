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
from utils import AnalysisMetadata, timer

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
def bulk_save(
    sources: list[DNAFeature],
    effects: list[RegulatoryEffectObservation],
    effect_directions: list[RegulatoryEffectObservation],
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


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, accession_ids, analysis, ref_genome, delimiter=","):
    experiment = analysis.experiment
    cell_line = experiment.biosamples.first().cell_line_name
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources: list[DNAFeature] = []
    effects: list[RegulatoryEffectObservation] = []
    effect_directions: list[FacetValue] = []
    for line in reader:
        chrom_name = line["seqnames"]

        ths_start = int(line["start"])
        ths_end = int(line["end"])
        dhs_location = NumericRange(ths_start, ths_end, "[]")

        try:
            dhs = DNAFeature.objects.get(
                experiment_accession=experiment,
                chrom_name=chrom_name,
                location=dhs_location,
                ref_genome=ref_genome,
                feature_type=DNAFeatureType.CAR,
            )
        except DNAFeature.DoesNotExist as e:
            print(f"{cell_line} {chrom_name}:{dhs_location} {ref_genome}")
            raise e

        sources.append(dhs)

        effect_size_field = line["logFC"].strip()
        if effect_size_field == "":
            effect_size = None
        else:
            effect_size = float(effect_size_field)

        significance = float(line["minusLog10PValue"])
        if significance < 2:  # p-value < 0.01, we're being stricter about significance with this data set
            direction = DIR_FACET_VALUES["Non-significant"]
        elif effect_size > 0:
            direction = DIR_FACET_VALUES["Enriched Only"]
        elif effect_size < 0:
            direction = DIR_FACET_VALUES["Depleted Only"]
        else:
            direction = None
        effect = RegulatoryEffectObservation(
            accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
            experiment=experiment,
            experiment_accession=experiment,
            analysis=analysis,
            facet_num_values={
                RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                # significance is -log10(actual significance), but we want significance between 0 and 1
                # we perform the inverse operation.
                RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: pow(10, -float(significance)),
                # significance is -log10(actual p-value), so raw_p_value uses the inverse operation
                RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: pow(10, -float(significance)),
                RegulatoryEffectObservation.Facet.AVG_COUNTS_PER_MILLION.value: float(line["input_avg_counts.cpm"]),
            },
        )
        effects.append(effect)
        effect_directions.append(direction)
    bulk_save(sources, effects, effect_directions)


def unload_analysis(analysis_metadata):
    analysis = Analysis.objects.get(
        experiment_id=analysis_metadata.experiment_accession_id, name=analysis_metadata.name
    )
    RegulatoryEffectObservation.objects.filter(analysis=analysis).delete()
    analysis_metadata.db_del(analysis)


def check_filename(analysis_filename: str):
    if len(analysis_filename) == 0:
        raise ValueError(f"wgCERES analysis filename '{analysis_filename}' must not be blank")


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
        for ceres_file, file_info, _delimiter in analysis_metadata.metadata():
            load_reg_effects(
                ceres_file,
                accession_ids,
                analysis,
                file_info.ref_genome,
                "\t",
            )
