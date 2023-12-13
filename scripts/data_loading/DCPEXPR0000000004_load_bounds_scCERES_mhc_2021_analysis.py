import csv
from io import StringIO

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

from .db import bulk_reo_save, reo_entry

DIR_FACET = Facet.objects.get(name="Direction")
DIR_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=DIR_FACET.id).all()}


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, accession_ids, analysis, ref_genome, ref_genome_patch, delimiter=","):
    experiment = analysis.experiment
    experiment_id = experiment.id
    experiment_accession_id = experiment.accession_id
    analysis_accession_id = analysis.accession_id
    cell_line = experiment.biosamples.first().cell_line_name
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    effects = StringIO()
    effect_directions = StringIO()
    sources = StringIO()
    target_genes = StringIO()
    grnas = {}
    with ReoIds() as reo_ids:
        for i, line in enumerate(reader):
            # every other line in this file is basically a duplicate of the previous line
            if i % 2 == 0:
                continue

            grna_label = line["grna"]
            grna_info = grna_label.split("-")

            # Skip non-targeting guides
            if not grna_info[0].startswith("chr"):
                continue

            reo_id = reo_ids.next_id()

            if grna_label not in grnas:
                grna_type = line["type"]

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

                try:
                    grnas[grna_label] = DNAFeature.objects.filter(
                        experiment_accession=experiment,
                        chrom_name=chrom_name,
                        location=grna_location,
                        strand=strand,
                        misc__grna=grna_label,
                        ref_genome=ref_genome,
                        feature_type=DNAFeatureType.GRNA,
                    ).values_list("id", flat=True)[0]
                except IndexError as e:
                    print(
                        f"{grna_label} {cell_line} {chrom_name}:{grna_location} {ref_genome} {ref_genome_patch} {DNAFeatureType.GRNA}"
                    )
                    raise e
            sources.write(f"{reo_id}\t{grnas[grna_label]}\n")

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

            target_gene_id = DNAFeature.objects.filter(
                ref_genome=ref_genome, ensembl_id=line["gene_stable_id"]
            ).values_list("id", flat=True)

            try:
                target_genes.write(f"{reo_id}\t{target_gene_id[0]}\n")
            except IndexError as ie:
                print(f'"{ref_genome}", "{line["gene_stable_id"]}"')
                raise ie

            facet_num_values = {
                RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: float(line["p_val"]),
                RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: significance,
            }

            effects.write(
                reo_entry(
                    id_=reo_id,
                    accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
                    experiment_id=experiment_id,
                    experiment_accession_id=experiment_accession_id,
                    analysis_accession_id=analysis_accession_id,
                    facet_num_values=facet_num_values,
                )
            )
            effect_directions.write(f"{reo_id}\t{direction.id}\n")

    bulk_reo_save(effects, effect_directions, sources, target_genes)


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
        for ceres_file, file_info, delimiter in analysis_metadata.metadata():
            load_reg_effects(
                ceres_file,
                accession_ids,
                analysis,
                file_info.ref_genome,
                file_info.ref_genome_patch,
                delimiter,
            )
