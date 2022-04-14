import csv
import time
from functools import lru_cache

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNARegion, Facet, FacetValue, FeatureAssembly
from utils import FileMetadata, get_delimiter, timer

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


@lru_cache(maxsize=1)
def get_pos_assemblies(chrom_name, ref_genome):
    return list(
        FeatureAssembly.objects.filter(
            chrom_name=chrom_name,
            strand="+",
            ref_genome=ref_genome,
            feature_type="gene",
        )
        .order_by("location")
        .all()
    )


@lru_cache(maxsize=1)
def get_neg_assemblies(chrom_name, ref_genome):
    return list(
        FeatureAssembly.objects.filter(
            chrom_name=chrom_name,
            strand="-",
            ref_genome=ref_genome,
            feature_type="gene",
        )
        .order_by("location")
        .all()
    )


def find_pos_closest(dhs_midpoint, assemblies):
    start = 0
    end = len(assemblies)
    index = (end + start) // 2
    while True:
        assembly = assemblies[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest assembly.
            for i in range(-6, 7):
                new_assembly = assemblies[min(max(0, index + i), len(assemblies) - 1)]
                if abs(new_assembly.location.lower - dhs_midpoint) < abs(assembly.location.lower - dhs_midpoint):
                    assembly = new_assembly
            return assembly

        if assembly.location.lower >= dhs_midpoint:
            end = index
        elif assembly.location.lower < dhs_midpoint:
            start = index

        index = (end + start) // 2


def find_neg_closest(dhs_midpoint, assemblies):
    start = 0
    end = len(assemblies)
    index = (end + start) // 2
    while True:
        assembly = assemblies[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest assembly.
            for i in range(-6, 7):
                new_assembly = assemblies[min(max(0, index + i), len(assemblies) - 1)]
                if abs(new_assembly.location.upper - dhs_midpoint) < abs(assembly.location.upper - dhs_midpoint):
                    assembly = new_assembly
            return assembly

        if assembly.location.upper >= dhs_midpoint:
            end = index
        elif assembly.location.upper < dhs_midpoint:
            start = index

        index = (end + start) // 2


def get_closest_gene(chrom_name, ref_genome, dhs_midpoint):
    closest_pos_assembly = find_pos_closest(dhs_midpoint, get_pos_assemblies(chrom_name, ref_genome))

    closest_neg_assembly = find_neg_closest(dhs_midpoint, get_neg_assemblies(chrom_name, ref_genome))

    if closest_pos_assembly is None and closest_neg_assembly is None:
        closest_assembly = None
        distance = -1
        closest_gene = None
        gene_name = "No Gene"
    elif closest_pos_assembly is None:
        closest_assembly = closest_neg_assembly
        distance = abs(dhs_midpoint - closest_neg_assembly.location.upper)
    elif closest_neg_assembly is None or abs(dhs_midpoint - closest_pos_assembly.location.lower) <= abs(
        closest_neg_assembly.location.upper - dhs_midpoint
    ):
        closest_assembly = closest_pos_assembly
        distance = abs(dhs_midpoint - closest_pos_assembly.location.lower)
    else:
        closest_assembly = closest_neg_assembly
        distance = abs(closest_neg_assembly.location.upper - dhs_midpoint)

    if closest_assembly is not None:
        closest_gene = closest_assembly.feature
        gene_name = closest_assembly.name

    return closest_assembly, closest_gene, distance, gene_name


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load cCREs")
def load_ccres(ccres_file, source_file, ref_genome, ref_genome_patch, delimiter=",", cell_line=None):
    reader = csv.reader(ccres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    new_sites: list[DNARegion] = []
    facets: list[list[FacetValue]] = []
    print("Starting line 0")
    start_time = time.perf_counter()
    get_gene_cumulative_time = 0
    for i, line in enumerate(reader):
        if i % LOAD_BATCH_SIZE == 0 and i != 0:
            print(f"Saving {i - LOAD_BATCH_SIZE}-{i - 1}")
            bulk_save(new_sites)
            set_facets(new_sites, facets)
            end_time = time.perf_counter()
            print(f"Got genes in {get_gene_cumulative_time} s")
            print(f"Loaded {LOAD_BATCH_SIZE} cCREs in: {end_time - start_time} s")
            start_time = time.perf_counter()
            get_gene_cumulative_time = 0
            new_sites = []
            facets = []
            print(f"Starting line {i}")

        chrom_name, dhs_start_str, dhs_end_str, _, accession_id, ccre_categories = line

        if "_" in chrom_name:
            continue

        dhs_start = int(dhs_start_str)
        dhs_end = int(dhs_end_str)
        dhs_location = NumericRange(dhs_start, dhs_end, "[]")

        dhs_midpoint = (dhs_start + dhs_end) // 2

        get_closest_gene_start = time.perf_counter()
        closest_assembly, closest_gene, distance, gene_name = get_closest_gene(chrom_name, ref_genome, dhs_midpoint)
        get_closest_gene_end = time.perf_counter()
        get_gene_cumulative_time += get_closest_gene_end - get_closest_gene_start
        dhs = DNARegion(
            cell_line=cell_line,
            chromosome_name=chrom_name,
            closest_gene=closest_gene,
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
