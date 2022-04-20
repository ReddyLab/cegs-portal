import csv

from django.db import transaction
from django.db.models import IntegerField
from django.db.models.functions import Abs, Lower, Upper
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNARegion,
    EffectDirectionType,
    Experiment,
    FeatureAssembly,
    RegulatoryEffect,
)
from utils import ExperimentMetadata, timer


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
def bulk_save(sites: list[DNARegion], effects: list[RegulatoryEffect]):
    with transaction.atomic():
        print("Adding DNaseIHypersensitiveSites")
        DNARegion.objects.bulk_create(sites, batch_size=1000)

        print("Adding RegulatoryEffects")
        RegulatoryEffect.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffects")
        for site, effect in zip(sites, effects):
            effect.sources.add(site)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, experiment, cell_line, ref_genome, ref_genome_patch, region_source, delimiter=","):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sites: list[DNARegion] = []
    effects: list[RegulatoryEffect] = []
    for line in reader:
        chrom_name = line["chrom"]

        dhs_start = int(line["chromStart"])
        dhs_end = int(line["chromEnd"])
        dhs_midpoint = (dhs_start + dhs_end) // 2
        dhs_location = NumericRange(dhs_start, dhs_end, "[]")

        closest_pos_assembly = (
            FeatureAssembly.objects.annotate(dist=Abs(Lower("location", output_field=IntegerField()) - dhs_midpoint))
            .filter(
                chrom_name=chrom_name,
                strand="+",
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                feature__feature_type="gene",
            )
            .order_by("dist")
            .first()
        )

        closest_neg_assembly = (
            FeatureAssembly.objects.annotate(dist=Abs(Upper("location", output_field=IntegerField()) - dhs_midpoint))
            .filter(
                chrom_name=chrom_name,
                strand="-",
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                feature__feature_type="gene",
            )
            .order_by("dist")
            .first()
        )

        if closest_pos_assembly is None:
            closest_assembly = closest_neg_assembly
        elif closest_neg_assembly is None:
            closest_assembly = closest_pos_assembly
        elif closest_pos_assembly.dist <= closest_neg_assembly.dist:
            closest_assembly = closest_pos_assembly
        else:
            closest_assembly = closest_neg_assembly

        if closest_assembly is not None:
            distance = closest_assembly.dist
            closest_gene = closest_assembly.gene
            gene_name = closest_assembly.name
        else:
            distance = -1
            closest_gene = None
            gene_name = "No Gene"

        dhs = DNARegion(
            cell_line=cell_line,
            chromosome_name=chrom_name,
            closest_gene=closest_gene,
            closest_gene_distance=distance,
            closest_gene_name=gene_name,
            location=dhs_location,
            ref_genome=ref_genome,
            ref_genome_patch=ref_genome_patch,
            region_type="dhs",
            source=region_source,
        )
        sites.append(dhs)

        effect_size_field = line["wgCERES_score_top3_wg"].strip()
        if effect_size_field == "":
            effect_size = None
        else:
            effect_size = float(effect_size_field)

        effect = RegulatoryEffect(
            direction=EffectDirectionType(line["direction_wg"]).value,
            experiment=experiment,
            effect_size=effect_size,
            # line[pValue] is -log10(actual p-value), so raw_p_value uses the inverse operation
            raw_p_value=pow(10, -float(line["pValue"])),
            significance=float(line["pValue"]),
        )
        effects.append(effect)
    bulk_save(sites, effects)


def unload_reg_effects(experiment_metadata):
    experiment = Experiment.objects.get(name=experiment_metadata.name)
    RegulatoryEffect.objects.filter(experiment=experiment).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"wgCERES experiment filename '{experiment_filename}' must not be blank")


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
            file_info.cell_line,
            file_info.ref_genome,
            file_info.ref_genome_patch,
            experiment.other_files.all()[0],
            delimiter,
        )
