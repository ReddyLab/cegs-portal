import csv

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    Analysis,
    DNAFeature,
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
def load_reg_effects(reo_file, accession_ids, analysis, ref_genome, delimiter=","):
    experiment = analysis.experiment
    reader = csv.DictReader(reo_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources: list[DNAFeature] = []
    effects: list[RegulatoryEffectObservation] = []
    effect_directions: list[FacetValue] = []
    dhss = {}
    for line in reader:
        chrom_name = line["chrom"]

        dhs_start = int(line["chromStart"])
        dhs_end = int(line["chromEnd"])
        dhs_string = f"{chrom_name}:{dhs_start}-{dhs_end}:{ref_genome}"

        if dhs_string in dhss:
            dhs = dhss[dhs_string]
        else:
            dhs_location = NumericRange(dhs_start, dhs_end, "[]")
            dhs = DNAFeature.objects.get(
                experiment_accession_id=experiment.accession_id,
                chrom_name=chrom_name,
                location=dhs_location,
                ref_genome=ref_genome,
            )
            dhss[dhs_string] = dhs

        sources.append(dhs)

        effect_size_field = line["wgCERES_score_top3_wg"].strip()
        if effect_size_field == "":
            effect_size = None
        else:
            effect_size = float(effect_size_field)

        direction_line = line["direction_wg"]
        if direction_line == "non_sig":
            direction = DIR_FACET_VALUES["Non-significant"]
        elif direction_line == "enriched":
            direction = DIR_FACET_VALUES["Enriched Only"]
        elif direction_line == "depleted":
            direction = DIR_FACET_VALUES["Depleted Only"]
        elif direction_line == "both":
            direction = DIR_FACET_VALUES["Mixed"]
        else:
            direction = None
        effect = RegulatoryEffectObservation(
            accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
            experiment=experiment,
            experiment_accession=experiment,
            analysis=analysis,
            facet_num_values={
                RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                # line[pValue] is -log10(actual p-value), so raw_p_value uses the inverse operation
                RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: pow(10, -float(line["pValue"])),
                RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: float(line["pValue"]),
            },
        )
        effects.append(effect)
        effect_directions.append(direction)
    bulk_save(sources, effects, effect_directions)


def unload_reg_effects(analysis_metadata):
    analysis = Analysis.objects.get(
        experiment_id=analysis_metadata.experiment_accession_id, name=analysis_metadata.name
    )
    RegulatoryEffectObservation.objects.filter(analysis=analysis).delete()
    analysis_metadata.db_del(analysis)


def check_filename(analysis_filename: str):
    if len(analysis_filename) == 0:
        raise ValueError(f"wgCERES experiment filename '{analysis_filename}' must not be blank")


def run(analysis_filename):
    with open(analysis_filename) as analysis_file:
        analysis_metadata = AnalysisMetadata.json_load(analysis_file)
    check_filename(analysis_metadata.name)

    # Only run unload_reg_effects if you want to delete the experiment, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects(analysis_metadata)

    analysis = analysis_metadata.db_save()

    with AccessionIds(message=f"{analysis.accession_id}: {analysis.name}"[:200]) as accession_ids:
        for reo_file, file_info, delimiter in analysis_metadata.metadata():
            load_reg_effects(
                reo_file,
                accession_ids,
                analysis,
                file_info.ref_genome,
                delimiter,
            )
