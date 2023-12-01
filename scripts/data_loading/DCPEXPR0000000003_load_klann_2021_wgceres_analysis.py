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


@timer("Load Reg Effects")
def load_reg_effects(reo_file, accession_ids, analysis, ref_genome, ref_genome_patch, delimiter=","):
    experiment = analysis.experiment
    experiment_id = experiment.id
    experiment_accession_id = experiment.accession_id
    analysis_accession_id = analysis.accession_id
    reader = csv.DictReader(reo_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources = StringIO()
    effects = StringIO()
    effect_directions = StringIO()
    dhss = {}

    with ReoIds() as reo_ids:
        for reo_id, line in zip(reo_ids, reader):
            try:
                chrom_name = line["chrom"]
            except KeyError as ke:
                print(f"delimiter: '{delimiter}'")
                print(line)
                raise ke

            dhs_start = int(line["chromStart"])
            dhs_end = int(line["chromEnd"])
            dhs_string = f"{chrom_name}:{dhs_start}-{dhs_end}:{ref_genome}"

            if dhs_string in dhss:
                dhs_id = dhss[dhs_string]
            else:
                dhs_id = DNAFeature.objects.filter(
                    experiment_accession=experiment,
                    chrom_name=chrom_name,
                    location=NumericRange(dhs_start, dhs_end, "[)"),
                    ref_genome=ref_genome,
                    feature_type=DNAFeatureType.DHS,
                ).values_list("id", flat=True)[0]
                dhss[dhs_string] = dhs_id

            sources.write(f"{reo_id}\t{dhs_id}\n")

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

            facet_num_values = json.dumps(
                {
                    RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                    # line[pValue] is -log10(actual p-value), so raw_p_value uses the inverse operation
                    RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: pow(10, -float(line["pValue"])),
                    # line[pValue] is -log10(actual p-value), but we want significance between 0 and 1
                    # we perform the inverse operation.
                    RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: pow(10, -float(line["pValue"])),
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
        for reo_file, file_info, delimiter in analysis_metadata.metadata():
            load_reg_effects(
                reo_file,
                accession_ids,
                analysis,
                file_info.ref_genome,
                file_info.ref_genome_patch,
                delimiter,
            )
