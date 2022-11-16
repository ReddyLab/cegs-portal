import csv

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
def bulk_save(grnas, effects, effect_directions, sources, source_facets, targets):
    with transaction.atomic():
        print("Adding gRNA Regions")
        DNAFeature.objects.bulk_create(grnas, batch_size=1000)

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
def load_reg_effects(
    ceres_file,
    accession_ids,
    gene_name_map,
    experiment,
    region_source,
    cell_line,
    ref_genome,
    ref_genome_patch,
    delimiter=",",
):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sites = []
    site_facets = []
    effects = []
    effect_directions = []
    targets = []
    grnas = {}
    existing_grna_facets = {}
    grnas_to_save = []
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
            grna_location = NumericRange(grna_start, grna_end, "[]")

            closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, grna_start, grna_end)

            try:
                region = DNAFeature.objects.get(
                    cell_line=cell_line,
                    chrom_name=chrom_name,
                    location=grna_location,
                    strand=strand,
                    ref_genome=ref_genome,
                    ref_genome_patch=ref_genome_patch,
                    feature_type=DNAFeatureType.GRNA,
                )
                existing_grna_facets[grna_id].update(region.facet_values.all())
            except DNAFeature.DoesNotExist:
                region = DNAFeature(
                    accession_id=accession_ids.incr(AccessionType.GRNA),
                    experiment_accession_id=experiment.accession_id,
                    cell_line=cell_line,
                    chrom_name=chrom_name,
                    closest_gene=closest_gene,
                    closest_gene_distance=distance,
                    closest_gene_name=gene_name,
                    closest_gene_ensembl_id=closest_gene.ensembl_id,
                    location=grna_location,
                    misc={"grna": grna_id},
                    ref_genome=ref_genome,
                    ref_genome_patch=ref_genome_patch,
                    feature_type=DNAFeatureType.GRNA,
                    source=region_source,
                    strand=strand,
                )
                grnas_to_save.append(region)
            grnas[grna_id] = region
        sites.append(region)

        grna_facets = set()
        grna_facets.add(GRNA_FACET_VALUES["Targeting"])
        site_facets.append(grna_facets - existing_grna_facets[grna_id])
        existing_grna_facets[grna_id].update(grna_facets)

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
            experiment_accession_id=experiment.accession_id,
            facet_num_values={
                RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: float(line["p_val"]),
                RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: significance,
            },
        )
        targets.append(target)
        effects.append(effect)
        effect_directions.append(direction)
    bulk_save(grnas_to_save, effects, effect_directions, sites, site_facets, targets)


def gene_ensembl_mapping(features_file):
    gene_name_map = {}
    with open(features_file, newline="") as facet_file:
        reader = csv.reader(facet_file, delimiter="\t")
        for row in reader:
            if row[2] != "Gene Expression":
                continue
            gene_name_map[row[1]] = row[0]

    return gene_name_map


def unload_reg_effects(experiment_metadata):
    experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    RegulatoryEffectObservation.objects.filter(experiment=experiment).delete()
    for file in experiment.other_files.all():
        DNAFeature.objects.filter(source=file).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"scCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename, features_file):
    with open(experiment_filename) as experiment_file:
        experiment_metadata = ExperimentMetadata.json_load(experiment_file)
    check_filename(experiment_metadata.name)

    # Only run unload_reg_effects if you want to delete the experiment, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects(experiment_metadata)

    experiment = experiment_metadata.db_save()

    gene_name_map = gene_ensembl_mapping(features_file)

    with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
        for i, meta in enumerate(experiment_metadata.metadata()):
            ceres_file, file_info, _delimiter = meta
            load_reg_effects(
                ceres_file,
                accession_ids,
                gene_name_map,
                experiment,
                experiment.other_files.all()[i],
                file_info.cell_line,
                file_info.ref_genome,
                file_info.ref_genome_patch,
                "\t",
            )
