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

GRNA_FACET = Facet.objects.get(name="gRNA Type")
GRNA_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_FACET.id).all()}

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
def bulk_save(effects, effect_directions, sources, source_facets, targets):
    with transaction.atomic():
        print("Adding RegulatoryEffectObservations")
        RegulatoryEffectObservation.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding gRNA type facets to gRNA regions")
        for source, facets in zip(sources, source_facets):
            source.facet_values.add(*facets)

    with transaction.atomic():
        print("Adding effect directions to effects")
        for effect, direction in zip(effects, effect_directions):
            effect.facet_values.add(direction)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffectObservations")
        for source, effect in zip(sources, effects):
            effect.sources.add(source)
        print("Adding targets to RegulatoryEffectObservations")
        for target, effect in zip(targets, effects):
            effect.targets.add(target)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, accession_ids, gene_name_map, analysis, ref_genome, delimiter=","):
    experiment = analysis.experiment
    cell_line = experiment.biosamples.first().cell_line_name
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources = []
    source_facets = []
    effects = []
    effect_directions = []
    targets = []
    grnas = {}
    existing_grna_facets = {}
    dne_genes = set()
    for line in reader:
        target_gene = line["target_gene"]

        if target_gene in TRIM_GENE_NAMES:
            target_gene = target_gene[:-2]

        grna_id = line["grna"]
        if grna_id in grnas:
            region = grnas[grna_id]
        else:
            existing_grna_facets[grna_id] = set()
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
                region = DNAFeature.objects.get(
                    experiment_accession=experiment,
                    chrom_name=chrom_name,
                    location=grna_location,
                    strand=strand,
                    misc__grna=grna_id,
                    ref_genome=ref_genome,
                    feature_type=DNAFeatureType.GRNA,
                )
            except DNAFeature.DoesNotExist as e:
                print(f"{cell_line} {chrom_name}:{grna_location} {ref_genome}")
                raise e
            grnas[grna_id] = region
        sources.append(region)

        grna_facets = set()
        grna_facets.add(GRNA_FACET_VALUES["Targeting"])
        source_facets.append(grna_facets - existing_grna_facets[grna_id])

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

        try:
            target = DNAFeature.objects.get(ref_genome=ref_genome, ensembl_id=gene_name_map[target_gene])
        except DNAFeature.MultipleObjectsReturned:
            target = DNAFeature.objects.get(
                ref_genome=ref_genome, ensembl_id=gene_name_map[target_gene], chrom_name="chrX"
            )
        except DNAFeature.DoesNotExist:
            if gene_name_map[target_gene] not in dne_genes:
                print(f"Not Found\t{gene_name_map[target_gene]}\t{target_gene}")
                dne_genes.add(gene_name_map[target_gene])
            continue
        except Exception as e:
            print(f"Unknown error\t{gene_name_map[target_gene]}\t{target_gene}")
            raise e

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
        targets.append(target)
        effects.append(effect)
        effect_directions.append(direction)
    bulk_save(effects, effect_directions, sources, source_facets, targets)


def gene_ensembl_mapping(features_file):
    gene_name_map = {}
    with open(features_file, newline="") as facet_file:
        reader = csv.reader(facet_file, delimiter="\t")
        for row in reader:
            if row[2] != "Gene Expression":
                continue
            gene_name_map[row[1]] = row[0]

    return gene_name_map


def unload_reg_effects(analysis_metadata):
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

    # Only run unload_reg_effects if you want to delete the analysis, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects(analysis_metadata)

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
