import csv
import os.path

from django.db import transaction
from django.db.models import IntegerField
from django.db.models.functions import Abs, Lower, Upper
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNaseIHypersensitiveSite,
    Experiment,
    GeneAssembly,
    RegulatoryEffect,
)
from utils import ExperimentData, ExperimentFile, timer


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
def bulk_save(sites, effects):
    with transaction.atomic():
        print("Adding DNaseIHypersensitiveSites")
        DNaseIHypersensitiveSite.objects.bulk_create(sites, batch_size=1000)

        print("Adding RegulatoryEffects")
        RegulatoryEffect.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffects")
        for site, effect in zip(sites, effects):
            effect.sources.add(site)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, experiment, cell_line, ref_genome, ref_genome_patch):
    reader = csv.DictReader(ceres_file, delimiter="\t", quoting=csv.QUOTE_NONE)
    sites = []
    effects = []
    for line in reader:
        strand = line["strand"]
        if strand == ".":
            strand = None
        chrom_name = line["chrom"]

        dhs_start = int(line["chromStart"])
        dhs_end = int(line["chromEnd"])
        dhs_midpoint = (dhs_start + dhs_end) // 2
        dhs_location = NumericRange(dhs_start, dhs_end, "[]")

        closest_pos_assembly = (
            GeneAssembly.objects.annotate(dist=Abs(Lower("location", output_field=IntegerField()) - dhs_midpoint))
            .filter(chrom_name=chrom_name, strand="+", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch)
            .order_by("dist")
            .first()
        )

        closest_neg_assembly = (
            GeneAssembly.objects.annotate(dist=Abs(Upper("location", output_field=IntegerField()) - dhs_midpoint))
            .filter(chrom_name=chrom_name, strand="-", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch)
            .order_by("dist")
            .first()
        )

        if closest_pos_assembly.dist <= closest_neg_assembly.dist:
            closest_assembly = closest_pos_assembly
        else:
            closest_assembly = closest_neg_assembly
        distance = closest_assembly.dist
        closest_gene = closest_assembly.gene
        gene_name = closest_assembly.name

        dhs = DNaseIHypersensitiveSite(
            cell_line=cell_line,
            chromosome_name=chrom_name,
            closest_gene=closest_gene,
            closest_gene_distance=distance,
            closest_gene_name=gene_name,
            location=dhs_location,
            ref_genome=ref_genome,
            ref_genome_patch=ref_genome_patch,
            strand=strand,
        )
        sites.append(dhs)

        score = line["wgCERES_score_top3_wg"].strip()
        if score == "":
            score = None

        effect = RegulatoryEffect(
            direction=line["direction_wg"], experiment=experiment, score=score, significance=line["pValue"]
        )
        effects.append(effect)
    bulk_save(sites, effects)


def unload_reg_effects():
    Experiment.objects.all().delete()
    DNaseIHypersensitiveSite.objects.all().delete()
    RegulatoryEffect.objects.all().delete()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"wgCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename):
    check_filename(experiment_filename)

    # Only run unload_reg_effects if you want to delete all the gencode data in the db.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects()

    with open(experiment_filename) as experiment_file:
        base_path = os.path.dirname(experiment_file.name)
        experiment_file = ExperimentFile.json_load(experiment_file)

    experiment = Experiment(name=experiment_file.name)
    experiment.save()

    for data in experiment_file.data:
        if data.datatype == ExperimentData.WGCERES_DATA:
            with open(os.path.join(base_path, data.filename), "r", newline="") as ceres_file:
                load_reg_effects(ceres_file, experiment, data.cell_line, data.ref_genome, data.ref_genome_patch)
