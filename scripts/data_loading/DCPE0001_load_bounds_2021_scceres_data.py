import csv

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNARegion,
    EffectDirectionType,
    Experiment,
    FeatureAssembly,
    RegulatoryEffect,
)
from utils import ExperimentMetadata, timer

from . import get_closest_gene


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
def bulk_save(sites, effects, target_assemblies):
    with transaction.atomic():
        print("Adding gRNA Regions")
        DNARegion.objects.bulk_create(sites, batch_size=1000)

        print("Adding RegulatoryEffects")
        RegulatoryEffect.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffects")
        for site, effect in zip(sites, effects):
            effect.sources.add(site)
        for assembly, effect in zip(target_assemblies, effects):
            effect.target_assemblies.add(assembly)
            effect.targets.add(assembly.feature)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, experiment, region_source, cell_line, ref_genome, ref_genome_patch, delimiter=","):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sites = []
    effects = []
    target_assembiles = []
    for line in reader:
        grna_info = line["grna"].split("-")

        if not grna_info[0].startswith("chr"):
            continue

        if len(grna_info) == 5:
            chrom_name, grna_start_str, grna_end_str, strand, _grna_seq = grna_info
        elif len(grna_info) == 6:
            chrom_name, grna_start_str, grna_end_str, _x, _y, _grna_seq = grna_info
            strand = "-"

        grna_start = int(grna_start_str)
        grna_end = int(grna_end_str)
        grna_location = NumericRange(grna_start, grna_end, "[]")

        closest_gene, closest_assembly, distance, gene_name = get_closest_gene(
            chrom_name, ref_genome, grna_start, grna_end
        )

        region = DNARegion(
            cell_line=cell_line,
            chrom_name=chrom_name,
            closest_gene=closest_gene,
            closest_gene_assembly=closest_assembly,
            closest_gene_distance=distance,
            closest_gene_name=gene_name,
            location=grna_location,
            misc={"grna": line["grna"]},
            ref_genome=ref_genome,
            ref_genome_patch=ref_genome_patch,
            region_type="grna",
            source=region_source,
            strand=strand,
        )
        sites.append(region)

        significance = float(line["pval_fdr_corrected"])
        effect_size = float(line["avg_logFC"])
        if significance >= 0.01:
            direction = EffectDirectionType.NON_SIGNIFICANT
        elif effect_size > 0:
            direction = EffectDirectionType.ENRICHED
        elif effect_size < 0:
            direction = EffectDirectionType.DEPLETED
        else:
            direction = EffectDirectionType.NON_SIGNIFICANT

        temp_target_assembly = FeatureAssembly.objects.filter(
            ref_genome=ref_genome, ref_genome_patch=ref_genome_patch, name=line["gene_symbol"]
        )
        if temp_target_assembly is None:
            print(f"Gene Name: {line['gene_symbol']}")
            assert temp_target_assembly is not None
        assert temp_target_assembly.count() == 1
        target_assembly = temp_target_assembly.first()

        effect = RegulatoryEffect(
            direction=direction.value,
            experiment=experiment,
            effect_size=effect_size,
            significance=significance,
            raw_p_value=line["p_val"],
        )
        target_assembiles.append(target_assembly)
        effects.append(effect)
    bulk_save(sites, effects, target_assembiles)


def unload_reg_effects(experiment_metadata):
    experiment = Experiment.objects.get(name=experiment_metadata.name)
    RegulatoryEffect.objects.filter(experiment=experiment).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"scCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename):
    with open(experiment_filename) as experiment_file:
        experiment_metadata = ExperimentMetadata.json_load(experiment_file)
    check_filename(experiment_metadata.name)
    experiment = experiment_metadata.db_save()

    # Only run unload_reg_effects if you want to delete all the gencode data in the db.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects(experiment_metadata)

    for ceres_file, file_info, delimiter in experiment_metadata.metadata():
        load_reg_effects(
            ceres_file,
            experiment,
            experiment.other_files.all()[0],
            file_info.cell_line,
            file_info.ref_genome,
            file_info.ref_genome_patch,
            delimiter,
        )
