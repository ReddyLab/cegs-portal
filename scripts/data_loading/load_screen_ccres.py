import csv
import os.path
import time
from io import StringIO

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    Facet,
    FacetValue,
)
from cegs_portal.utils.db_ids import FeatureIds
from utils import get_delimiter, timer
from utils.file import FileMetadata

from . import get_closest_gene
from .db import bulk_feature_facet_save, bulk_feature_save, feature_entry

LOAD_BATCH_SIZE = 100_000

CCRE_FACET = Facet.objects.get(name="cCRE Category")
CCRE_FACET_VALUES = {facet.value: facet.id for facet in FacetValue.objects.filter(facet_id=CCRE_FACET.id).all()}


def get_facets(facet_string):
    facet_values = facet_string.split(",")
    return [CCRE_FACET_VALUES[value] for value in facet_values]


# loading does buffered writes to the DB, with a buffer size of LOAD_BATCH_SIZE annotations
@timer("Load cCREs")
def load_ccres(ccres_file, accession_ids, source_file, ref_genome, ref_genome_patch, delimiter=",", cell_line=None):
    reader = csv.reader(ccres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    source_file_id = source_file.id
    ccres = set()
    start_time = time.perf_counter()

    new_ccres = StringIO()
    new_feature_facets = StringIO()
    with FeatureIds() as feature_ids:
        for i, line in enumerate(reader, start=1):
            if i % LOAD_BATCH_SIZE == 0:
                bulk_feature_save(new_ccres)
                bulk_feature_facet_save(new_feature_facets)
                end_time = time.perf_counter()
                print(f"Loaded {LOAD_BATCH_SIZE} cCREs in: {end_time - start_time} s")
                start_time = time.perf_counter()
                new_ccres.close()
                new_ccres = StringIO()
                new_feature_facets.close()
                new_feature_facets = StringIO()

            chrom_name, ccre_start_str, ccre_end_str, _, screen_accession_id, ccre_categories = line

            if "_" in chrom_name:
                continue

            ccre_start = int(ccre_start_str)
            ccre_end = int(ccre_end_str)

            # There shouldn't be duplicate cCREs, but the liftover from
            # hg38 to hg37 is imperfect and results in some duplicates
            if (chrom_name, ccre_start, ccre_end) in ccres:
                continue
            else:
                ccres.add((chrom_name, ccre_start, ccre_end))

            # Doesn't use the iterable features of FeatureIds so we don't skip ids when a cCRE is skipped
            # due to not being unique
            feature_id = feature_ids.next_id()
            ccre_location = f"[{ccre_start},{ccre_end})"
            closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, ccre_start, ccre_end)
            closest_gene_ensembl_id = closest_gene["ensembl_id"] if closest_gene is not None else "\\N"

            new_ccres.write(
                feature_entry(
                    id_=feature_id,
                    accession_id=accession_ids.incr(AccessionType.CCRE),
                    cell_line=cell_line,
                    chrom_name=chrom_name,
                    location=ccre_location,
                    closest_gene_id=closest_gene["id"],
                    closest_gene_distance=distance,
                    closest_gene_name=gene_name,
                    closest_gene_ensembl_id=closest_gene_ensembl_id,
                    genome_assembly=ref_genome,
                    genome_assembly_patch=ref_genome_patch,
                    feature_type=DNAFeatureType.CCRE,
                    source_file_id=source_file_id,
                    misc={"screen_accession_id": screen_accession_id},
                )
            )
            feature_facets_ids = get_facets(ccre_categories)
            for facet_id in feature_facets_ids:
                new_feature_facets.write(f"{feature_id}\t{facet_id}\n")

    bulk_feature_save(new_ccres)
    bulk_feature_facet_save(new_feature_facets)
    end_time = time.perf_counter()
    print(f"Loaded {LOAD_BATCH_SIZE} cCREs in: {end_time - start_time}s")
    new_ccres.close()
    new_feature_facets.close()


@timer("Unloading CCREs", level=1)
def unload_ccres(file_metadata):
    DNAFeature.objects.filter(source_file=file_metadata.file).delete()
    file_metadata.db_del()


def check_filename(ccre_data: str):
    if len(ccre_data) == 0:
        raise ValueError(f"cCRE data filename '{ccre_data}' must not be blank")


def full_data_filepath(ccre_file, data_filename):
    base_path = os.path.dirname(ccre_file)
    return os.path.join(base_path, data_filename)


def run(ccre_data: str, ref_genome: str, ref_genome_patch: str):
    with open(ccre_data) as file:
        file_metadata = FileMetadata.json_load(file)

    check_filename(file_metadata.filename)

    # Only run unload_ccres if you want to delete all the ccres loaded by ccre_data file.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_ccres() uncommented is not, strictly, idempotent.
    # unload_ccres(file_metadata)

    source_file = file_metadata.db_save()

    with open(full_data_filepath(ccre_data, file_metadata.filename)) as ccres_file, AccessionIds(
        message=f"cCRE for {ref_genome}.{ref_genome_patch}"
    ) as accession_ids:
        load_ccres(
            ccres_file,
            accession_ids,
            source_file,
            ref_genome,
            ref_genome_patch,
            delimiter=get_delimiter(file_metadata.filename),
        )
