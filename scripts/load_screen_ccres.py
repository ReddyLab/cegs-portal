import csv

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import IntegerField
from django.db.models.functions import Abs, Lower, Upper
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNaseIHypersensitiveSite, GeneAssembly
from utils import FileMetadata, get_delimiter, timer


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
def bulk_save(sites):
    with transaction.atomic():
        print("Adding DNaseIHypersensitiveSites")
        DNaseIHypersensitiveSite.objects.bulk_create(sites, batch_size=1000)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load cCREs")
def load_ccres(ccres_file, source_file, ref_genome, ref_genome_patch, delimiter=",", cell_line=None):
    reader = csv.reader(ccres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    new_sites = []
    new_dhs_set = set()
    for i, line in enumerate(reader):
        if i % 100_000 == 0:
            print(f"line {i + 1}")
        chrom_name, dhs_start, dhs_end, name = line
        dhs_start = int(dhs_start)
        dhs_end = int(dhs_end)
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

        try:
            dhs = DNaseIHypersensitiveSite.objects.get(chromosome_name=chrom_name, location=dhs_location)
        except ObjectDoesNotExist:
            dhs = DNaseIHypersensitiveSite(
                cell_line=cell_line,
                chromosome_name=chrom_name,
                closest_gene=closest_gene,
                closest_gene_assembly=closest_assembly,
                closest_gene_distance=distance,
                closest_gene_name=gene_name,
                location=dhs_location,
                ref_genome=ref_genome,
                ref_genome_patch=ref_genome_patch,
                screen_accession_id=name,
                source=source_file,
            )
            new_sites.append(dhs)
        else:
            dhs_loc = f"{chrom_name}: {dhs_start}-{dhs_end}"
            if dhs_loc not in new_dhs_set:
                new_dhs_set.add(dhs_loc)
                print(dhs_loc)

            dhs.screen_accession_id = name
            dhs.source = source_file
            dhs.save()
    print(f"Old DHS Count: {len(dhs_loc)}")
    bulk_save(new_sites)


def check_filename(ccre_data: str):
    if len(ccre_data) == 0:
        raise ValueError(f"cCRE data filename '{ccre_data}' must not be blank")


def run(ccre_data: str, ref_genome: str, ref_genome_patch: str):
    with open(ccre_data) as file:
        file_metadata = FileMetadata.json_load(file)

    check_filename(file_metadata.filename)
    source_file = file_metadata.db_save()

    # Only run unload_reg_effects if you want to delete all the gencode data in the db.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_ccres(ccre_data)

    with open(file_metadata.full_data_filepath) as ccres_file:
        load_ccres(
            ccres_file, source_file, ref_genome, ref_genome_patch, delimiter=get_delimiter(file_metadata.data_filename)
        )
