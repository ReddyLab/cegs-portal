import csv

from django.db import transaction
from django.db.models import F, IntegerField
from django.db.models.functions import Abs, Lower, Upper
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNARegion, Facet, FacetValue, FeatureAssembly
from utils import FileMetadata, get_delimiter, timer

LOAD_BATCH_SIZE = 10_000

CCRE_FACET = Facet.objects.get(name="cCRE Category")
CCRE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=CCRE_FACET.id).all()}


@timer("Save cCREs")
def bulk_save(sites):
    with transaction.atomic():
        DNARegion.objects.bulk_create(sites, batch_size=1000)


def get_facets(facet_string):
    facet_values = facet_string.split(",")
    return [CCRE_FACET_VALUES[value] for value in facet_values]


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load cCREs")
def load_ccres(ccres_file, source_file, ref_genome, ref_genome_patch, delimiter=",", cell_line=None):
    reader = csv.reader(ccres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    new_sites: list[DNARegion] = []
    facets: list[list[FacetValue]] = []
    print("Starting line 0")
    for i, line in enumerate(reader):
        if i % LOAD_BATCH_SIZE == 0 and i != 0:
            print(f"Saving {i - LOAD_BATCH_SIZE}-{i - 1}")
            bulk_save(new_sites)
            for site, facet_qset in zip(new_sites, facets):
                for facet in facet_qset:
                    site.facet_values.add(facet)
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

        closest_pos_assembly = (
            FeatureAssembly.objects.annotate(dist=Abs(Lower(F("location"), output_field=IntegerField()) - dhs_midpoint))
            .filter(chrom_name=chrom_name, strand="+", ref_genome=ref_genome, feature__feature_type="gene")
            .order_by("dist")
            .first()
        )

        closest_neg_assembly = (
            FeatureAssembly.objects.annotate(dist=Abs(Upper(F("location"), output_field=IntegerField()) - dhs_midpoint))
            .filter(chrom_name=chrom_name, strand="-", ref_genome=ref_genome, feature__feature_type="gene")
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
            closest_gene = closest_assembly.feature
            gene_name = closest_assembly.name
        else:
            distance = -1
            closest_gene = None
            gene_name = "No Gene"

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
    for site, facet_qset in zip(new_sites, facets):
        for facet in facet_qset:
            site.facet_values.add(facet)


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
