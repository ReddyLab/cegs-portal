import csv
import os.path

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNaseIHypersensitiveSite,
    EffectDirectionType,
    Experiment,
    ExperimentDataFile,
    GeneAssembly,
    RegulatoryEffect,
)
from utils import ExperimentDataType, ExperimentFile, timer


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
def bulk_save(sites, new_sites, effects, target_assemblies):
    with transaction.atomic():
        print("Adding DNaseIHypersensitiveSites")
        DNaseIHypersensitiveSite.objects.bulk_create(new_sites, batch_size=1000)

        print("Adding RegulatoryEffects")
        RegulatoryEffect.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffects")
        for site, effect in zip(sites, effects):
            effect.sources.add(site)
        for assembly, effect in zip(target_assemblies, effects):
            effect.target_assemblies.add(assembly)
            effect.targets.add(assembly.gene)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, experiment, cell_line, ref_genome, ref_genome_patch, delimiter=","):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sites = []
    new_sites = []
    effects = []
    target_assembiles = []
    new_dhs_set = set()
    for line in reader:
        strand = line["strand"]
        if strand == ".":
            strand = None
        chrom_name = line["dhs_chrom"]

        dhs_start = int(line["dhs_start"])
        dhs_end = int(line["dhs_end"])
        dhs_location = NumericRange(dhs_start, dhs_end, "[]")

        try:
            dhs = DNaseIHypersensitiveSite.objects.get(chromosome_name=chrom_name, location=dhs_location)
        except ObjectDoesNotExist:
            dhs_loc = f"{chrom_name}: {dhs_start}-{dhs_end}"
            if dhs_loc not in new_dhs_set:
                new_dhs_set.add(dhs_loc)
                print(dhs_loc)
            dhs = DNaseIHypersensitiveSite(
                cell_line=cell_line,
                chromosome_name=chrom_name,
                closest_gene=None,
                closest_gene_assembly=None,
                closest_gene_distance=0,
                closest_gene_name="",
                location=dhs_location,
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                strand=strand,
            )
            dhs.save()
        sites.append(dhs)

        significance = float(line["pval_empirical"])
        effect_size = float(line["avg_logFC"])
        if significance >= 0.01:
            direction = EffectDirectionType.NON_SIGNIFICANT
        elif effect_size > 0:
            direction = EffectDirectionType.ENRICHED
        elif effect_size < 0:
            direction = EffectDirectionType.DEPLETED
        else:
            direction = EffectDirectionType.NON_SIGNIFICANT

        target_assembly = (
            GeneAssembly.objects.filter(
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                name=line["gene_symbol"],
                location=NumericRange(int(line["start"]), int(line["end"]), "[]"),
            )
            .select_related("gene")
            .first()
        )
        if target_assembly is None:
            print(f"Gene Name: {line['gene_symbol']}")
            assert target_assembly is not None
        effect = RegulatoryEffect(
            direction=direction.value,
            experiment=experiment,
            effect_size=effect_size,
            significance=significance,
            raw_p_value=line["p_val"],
        )
        target_assembiles.append(target_assembly)
        effects.append(effect)
    print(f"New DHS Count: {len(new_sites)}")
    bulk_save(sites, new_sites, effects, target_assembiles)


def unload_reg_effects(experiment_name):
    experiment = Experiment.objects.get(name=experiment_name)
    RegulatoryEffect.objects.filter(experiment=experiment).delete()
    experiment.delete()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"scCERES experiment filename '{experiment_filename}' must not be blank")


def get_delimiter(filename):
    _, ext = os.path.splitext(filename)
    if ext == "csv":
        return ","
    elif ext == "tsv":
        return "\t"
    else:
        return ","


def run(experiment_filename):
    check_filename(experiment_filename)

    with open(experiment_filename) as experiment_file:
        base_path = os.path.dirname(experiment_file.name)
        experiment_file = ExperimentFile.json_load(experiment_file)

    experiment = Experiment(name=experiment_file.name)
    experiment.save()
    for data in experiment_file.data:
        data_file = ExperimentDataFile(
            cell_line=data.cell_line,
            experiment=experiment,
            filename=data.filename,
            ref_genome=data.ref_genome,
            ref_genome_patch=data.ref_genome_patch,
            significance_measure=data.significance_measure,
        )
        data_file.save()
        experiment.data_files.add(data_file)

    # Only run unload_reg_effects if you want to delete all the gencode data in the db.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects(experiment_file.name)

    for data in experiment_file.data:
        if data.datatype == ExperimentDataType.SCCERES_DATA:
            with open(os.path.join(base_path, data.filename), "r", newline="") as ceres_file:
                delimiter = get_delimiter(data.filename)
                load_reg_effects(
                    ceres_file, experiment, data.cell_line, data.ref_genome, data.ref_genome_patch, delimiter
                )
