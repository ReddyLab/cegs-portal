import csv
import json
from io import StringIO
from os import SEEK_SET

from django.db import connection, transaction
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
from utils.db_ids import ReoIds
from utils.experiment import AnalysisMetadata

DIR_FACET = Facet.objects.get(name="Direction")
DIR_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=DIR_FACET.id).all()}


def bulk_save(
    source_associations: StringIO,
    effects: StringIO,
    effect_directions: StringIO,
):
    with transaction.atomic(), connection.cursor() as cursor:
        effects.seek(0, SEEK_SET)
        print("Adding RegulatoryEffectObservations")
        cursor.copy_from(
            effects,
            "search_regulatoryeffectobservation",
            columns=(
                "id",
                "accession_id",
                "experiment_id",
                "experiment_accession_id",
                "analysis_accession_id",
                "facet_num_values",
                "archived",
                "public",
            ),
        )

    with transaction.atomic(), connection.cursor() as cursor:
        effect_directions.seek(0, SEEK_SET)
        print("Adding effect directions to effects")
        cursor.copy_from(
            effect_directions,
            "search_regulatoryeffectobservation_facet_values",
            columns=(
                "regulatoryeffectobservation_id",
                "facetvalue_id",
            ),
        )

    with transaction.atomic(), connection.cursor() as cursor:
        source_associations.seek(0, SEEK_SET)
        print("Adding sources to RegulatoryEffectObservations")
        cursor.copy_from(
            source_associations,
            "search_regulatoryeffectobservation_sources",
            columns=("regulatoryeffectobservation_id", "dnafeature_id"),
        )


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(reo_file, accession_ids, analysis, ref_genome, delimiter=","):
    experiment = analysis.experiment
    experiment_id = experiment.id
    experiment_accession_id = experiment.accession_id
    analysis_accession_id = analysis.accession_id
    reader = csv.DictReader(reo_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources = StringIO()
    effects = StringIO()
    effect_directions = StringIO()
    experiment = analysis.experiment

    with ReoIds() as reo_ids:
        for reo_id, line in zip(reo_ids, reader):
            chrom_name = line["seqnames"]

            car_start = int(line["start"])
            car_end = int(line["end"])

            car_id = DNAFeature.objects.filter(
                experiment_accession=experiment,
                chrom_name=chrom_name,
                location=NumericRange(car_start, car_end, "[)"),
                ref_genome=ref_genome,
                feature_type=DNAFeatureType.CAR,
            ).values_list("id", flat=True)[0]

            sources.write(f"{reo_id}\t{car_id}\n")

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

            facet_num_values = json.dumps(
                {
                    RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                    # significance is -log10(actual significance), but we want significance between 0 and 1
                    # we perform the inverse operation.
                    RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: pow(10, -float(significance)),
                    # significance is -log10(actual p-value), so raw_p_value uses the inverse operation
                    RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: pow(10, -float(significance)),
                    RegulatoryEffectObservation.Facet.AVG_COUNTS_PER_MILLION.value: float(line["input_avg_counts.cpm"]),
                }
            )

            effects.write(
                f"{reo_id}\t{accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS)}\t{experiment_id}\t{experiment_accession_id}\t{analysis_accession_id}\t{facet_num_values}\tfalse\ttrue\n"
            )
            effect_directions.write(f"{reo_id}\t{direction.id}\n")
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
