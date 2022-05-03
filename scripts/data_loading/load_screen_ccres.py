import csv
import time

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNARegion, Facet, FacetValue
from utils import FileMetadata, get_delimiter, timer

from . import get_closest_gene

LOAD_BATCH_SIZE = 10_000

CCRE_FACET = Facet.objects.get(name="cCRE Category")
CCRE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=CCRE_FACET.id).all()}


def bulk_save(sites):
    with transaction.atomic():
        DNARegion.objects.bulk_create(sites, batch_size=1000)


@timer("Set Facets", unit="s")
def set_facets(new_sites, facets):
    for site, facet_qset in zip(new_sites, facets):
        site.facet_values.add(*facet_qset)


def get_facets(facet_string):
    facet_values = facet_string.split(",")
    return [CCRE_FACET_VALUES[value] for value in facet_values]


# loading does buffered writes to the DB, with a buffer size of LOAD_BATCH_SIZE annotations
@timer("Load cCREs")
def load_ccres(ccres_file, source_file, ref_genome, ref_genome_patch, delimiter=",", cell_line=None):
    reader = csv.reader(ccres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    new_sites: list[DNARegion] = []
    facets: list[list[FacetValue]] = []
    print("Starting line 0")
    start_time = time.perf_counter()
    for i, line in enumerate(reader):
        if i % LOAD_BATCH_SIZE == 0 and i != 0:
            print(f"Saving {i - LOAD_BATCH_SIZE}-{i - 1}")
            bulk_save(new_sites)
            set_facets(new_sites, facets)
            end_time = time.perf_counter()
            print(f"Loaded {LOAD_BATCH_SIZE} cCREs in: {end_time - start_time} s")
            start_time = time.perf_counter()
            new_sites = []
            facets = []
            print(f"Starting line {i}")

        chrom_name, dhs_start_str, dhs_end_str, _, accession_id, ccre_categories = line

        if "_" in chrom_name:
            continue

        dhs_start = int(dhs_start_str)
        dhs_end = int(dhs_end_str)
        dhs_location = NumericRange(dhs_start, dhs_end, "[]")

        closest_assembly, distance, gene_name = get_closest_gene(ref_genome, chrom_name, dhs_start, dhs_end)
        dhs = DNARegion(
            cell_line=cell_line,
            chrom_name=chrom_name,
            closest_gene_assembly=closest_assembly,
            closest_gene_distance=distance,
            closest_gene_name=gene_name,
            location=dhs_location,
            ref_genome=ref_genome,
            ref_genome_patch=ref_genome_patch,
            misc={"screen_accession_id": accession_id},
            region_type="ccre",
            source=source_file,
        )
        new_sites.append(dhs)
        facets.append(get_facets(ccre_categories))

    bulk_save(new_sites)
    set_facets(new_sites, facets)
    end_time = time.perf_counter()
    print(f"Loaded {LOAD_BATCH_SIZE} cCREs in: {end_time - start_time} s")


def check_filename(ccre_data: str):
    if len(ccre_data) == 0:
        raise ValueError(f"cCRE data filename '{ccre_data}' must not be blank")


def run(ccre_data: str, ref_genome: str, ref_genome_patch: str):
    with open(ccre_data) as file:
        file_metadata = FileMetadata.json_load(file)

    check_filename(file_metadata.filename)
    source_file = file_metadata.db_save()

    with open(file_metadata.full_data_filepath) as ccres_file:
        load_ccres(
            ccres_file, source_file, ref_genome, ref_genome_patch, delimiter=get_delimiter(file_metadata.data_filename)
        )
