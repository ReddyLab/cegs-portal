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

# These gene names appear in the data and have a "version" ("".1") in a few instances.
# We don't know why. It's safe to remove the version for processing though.
TRIM_GENE_NAMES = [
    "HSPA14.1",
    "MATR3.1",
    "GGT1.1",
    "TMSB15B.1",
    "TBCE.1",
    "CYB561D2.1",
    "GOLGA8M.1",
    "LINC01238.1",
    "ARMCX5-GPRASP2.1",
    "LINC01505.1",
]


@timer("Load Reg Effects")
def load_reg_effects(ceres_file, accession_ids, gene_name_map, analysis, ref_genome, delimiter=","):
    experiment = analysis.experiment
    experiment_id = experiment.id
    experiment_accession_id = experiment.accession_id
    analysis_accession_id = analysis.accession_id
    cell_line = experiment.biosamples.first().cell_line_name
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources = StringIO()
    effects = StringIO()
    effect_directions = StringIO()
    targets = StringIO()
    grnas = {}
    target_genes = {}
    dne_genes = set()
    with ReoIds() as reo_ids:
        for line in reader:
            # Find sources
            grna_label = line["grna"]
            if grna_label not in grnas:
                strand = line["Strand"]
                chrom_name = line["chr"]
                grna_start = int(line["start"])
                grna_end = int(line["end"])

                if strand == "+":
                    bounds = "[)"
                elif strand == "-":
                    bounds = "(]"

                grna_location = NumericRange(grna_start, grna_end, bounds)

                try:
                    guide_id = DNAFeature.objects.filter(
                        experiment_accession=experiment,
                        chrom_name=chrom_name,
                        location=grna_location,
                        strand=strand,
                        misc__grna=grna_label,
                        ref_genome=ref_genome,
                        feature_type=DNAFeatureType.GRNA,
                    ).values_list("id", flat=True)[0]
                except IndexError as e:
                    print(f"{grna_label} {cell_line} {chrom_name}:{grna_location} {ref_genome} {DNAFeatureType.GRNA}")
                    raise e
                grnas[grna_label] = guide_id

            # Find targets
            target_gene = line["target_gene"]
            if target_gene in TRIM_GENE_NAMES:
                target_gene = target_gene[:-2]

            if target_gene not in target_genes:
                target_id = DNAFeature.objects.filter(
                    ref_genome=ref_genome, ensembl_id=gene_name_map[target_gene]
                ).values_list("id", flat=True)

                if len(target_id.all()) > 1:
                    target_id = DNAFeature.objects.filter(
                        ref_genome=ref_genome, ensembl_id=gene_name_map[target_gene], chrom_name="chrX"
                    ).values_list("id", flat=True)
                elif len(target_id.all()) == 0:
                    if gene_name_map[target_gene] not in dne_genes:
                        print(f"Not Found\t{gene_name_map[target_gene]}\t{target_gene}")
                        dne_genes.add(gene_name_map[target_gene])
                    continue
                target_genes[target_gene] = target_id[0]

            # Get REO data
            reo_id = reo_ids.next_id()

            sources.write(f"{reo_id}\t{grnas[grna_label]}\n")
            targets.write(f"{reo_id}\t{target_genes[target_gene]}\n")

            significance = float(line["p_val_adj"])
            effect_size = float(line["avg_log2FC"])
            if significance >= 0.01:
                direction = DIR_FACET_VALUES["Non-significant"]
            elif effect_size > 0:
                direction = DIR_FACET_VALUES["Enriched Only"]
            elif effect_size < 0:
                direction = DIR_FACET_VALUES["Depleted Only"]
            else:
                direction = DIR_FACET_VALUES["Non-significant"]

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

    bulk_reo_save(effects, effect_directions, sources, targets)


def gene_ensembl_mapping(features_file):
    gene_name_map = {}
    with open(features_file, newline="") as facet_file:
        reader = csv.reader(facet_file, delimiter="\t")
        for row in reader:
            if row[2] != "Gene Expression":
                continue
            gene_name_map[row[1]] = row[0]

    return gene_name_map


def unload_analysis(analysis_metadata):
    analysis = Analysis.objects.get(
        experiment_id=analysis_metadata.experiment_accession_id, name=analysis_metadata.name
    )
    RegulatoryEffectObservation.objects.filter(analysis=analysis).delete()
    analysis_metadata.db_del(analysis)


def check_filename(analysis_filename: str):
    if len(analysis_filename) == 0:
        raise ValueError(f"scCERES analysis filename '{analysis_filename}' must not be blank")


def run(analysis_filename, features_file):
    with open(analysis_filename) as analysis_file:
        analysis_metadata = AnalysisMetadata.json_load(analysis_file)
    check_filename(analysis_metadata.name)

    # Only run unload_analysis if you want to delete the analysis, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_analysis() uncommented is not, strictly, idempotent.
    # unload_analysis(analysis_metadata)

    analysis = analysis_metadata.db_save()

    gene_name_map = gene_ensembl_mapping(features_file)

    with AccessionIds(message=f"{analysis.accession_id}: {analysis.name}"[:200]) as accession_ids:
        for ceres_file, file_info, _delimiter in analysis_metadata.metadata():
            load_reg_effects(
                ceres_file,
                accession_ids,
                gene_name_map,
                analysis,
                file_info.ref_genome,
                "\t",
            )
