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


CORRECT_FEATURES = ["ENSG00000272333"]


def bulk_save(
    source_associations: StringIO,
    effects: StringIO,
    effect_directions: StringIO,
    target_associations: StringIO,
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
        target_associations.seek(0, SEEK_SET)
        print("Adding targets to RegulatoryEffectObservations")
        cursor.copy_from(
            target_associations,
            "search_regulatoryeffectobservation_targets",
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
    targets = StringIO()
    effects = StringIO()
    effect_directions = StringIO()
    dhss = {}

    with ReoIds() as reo_ids:
        for reo_id, line in zip(reo_ids, reader):
            chrom_name = line["dhs_chrom"]

            dhs_start = int(line["dhs_start"])
            dhs_end = int(line["dhs_end"])
            dhs_string = f"{chrom_name}:{dhs_start}-{dhs_end}:{ref_genome}"

            gene_start = int(line["start"]) - 1
            gene_end = int(line["end"])

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

            target_id = DNAFeature.objects.filter(
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                name=line["gene_symbol"],
                location=NumericRange(gene_start, gene_end, "[)"),
            ).values_list("id", flat=True)
            if len(target_id) > 1:
                # There is ONE instance where there are two genes with the same name
                # in the exact same location. This handles that situation.
                # The two gene IDs are ENSG00000272333 and ENSG00000105663.
                # I decided that ENSG00000272333 was the "correct" gene to use here
                # because it's the one that still exists in GRCh38.
                target_id = DNAFeature.objects.filter(
                    ref_genome=ref_genome,
                    ref_genome_patch=ref_genome_patch,
                    name=line["gene_symbol"],
                    location=NumericRange(gene_start, gene_end, "[)"),
                    ensembl_id__in=CORRECT_FEATURES,
                ).values_list("id", flat=True)

            try:
                targets.write(f"{reo_id}\t{target_id[0]}\n")
            except IndexError as ie:
                print(f"{ref_genome} {ref_genome_patch} {line['gene_symbol']} [{gene_start}, {gene_end})")
                raise ie

            facet_num_values = json.dumps(
                {
                    RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                    RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: float(line["p_val"]),
                    RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: significance,
                }
            )
            effects.write(
                f"{reo_id}\t{accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS)}\t{experiment_id}\t{experiment_accession_id}\t{analysis_accession_id}\t{facet_num_values}\tfalse\ttrue\n"
            )
            effect_directions.write(f"{reo_id}\t{direction.id}\n")
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
