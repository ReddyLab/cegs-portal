import csv
import json
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from os import SEEK_SET
from typing import Optional

from django.db import connection, transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import AccessionType, DNAFeature, DNAFeatureType

from .db_ids import FeatureIds


@dataclass
class CcreSource:
    _id: int
    chrom_name: str
    test_location: NumericRange
    cell_line: str
    closest_gene_id: int
    closest_gene_distance: int
    closest_gene_name: str
    closest_gene_ensembl_id: int
    source_file_id: int
    ref_genome: str
    experiment_accession_id: str
    ref_genome_patch: str = "0"
    _new_id: Optional[int] = None
    new_location: Optional[NumericRange] = None
    feature_type: DNAFeatureType = DNAFeatureType.CCRE
    misc: dict = field(default_factory=lambda: {"pseudo": True})


def save_ccres(ccres: StringIO):
    ccres.seek(0, SEEK_SET)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.copy_from(
            ccres,
            "search_dnafeature",
            columns=(
                "id",
                "accession_id",
                "cell_line",
                "chrom_name",
                "closest_gene_id",
                "closest_gene_distance",
                "closest_gene_name",
                "closest_gene_ensembl_id",
                "location",
                "ref_genome",
                "ref_genome_patch",
                "misc",
                "feature_type",
                "source_file_id",
                "experiment_accession_id",
                "archived",
                "public",
            ),
        )


def save_associations(associations):
    associations.seek(0, SEEK_SET)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.copy_from(
            associations, "search_dnafeature_associated_ccres", columns=("from_dnafeature_id", "to_dnafeature_id")
        )


def get_ccres(locs: list[tuple[str, int, int, str]]):
    chrom, _, _, ref_genome = locs[0]
    return DNAFeature.objects.filter(
        chrom_name=chrom,
        location__in=[NumericRange(loc[1], loc[2], "[)") for loc in locs],
        ref_genome=ref_genome,
        feature_type=DNAFeatureType.CCRE,
    ).values_list("id", flat=True)


def source_ccre_locs(closest_ccre_filename, ref_genome):
    ccres = defaultdict(list)
    with open(closest_ccre_filename, "r") as closest_ccres:
        ccre_reader = csv.reader(closest_ccres, delimiter="\t")
        for source_chr, source_start, source_end, ccre_chr, ccre_start, ccre_end in ccre_reader:
            source_start = int(source_start)
            source_end = int(source_end)
            ccre_start = int(ccre_start)
            ccre_end = int(ccre_end)
            ccres[(source_chr, source_start, source_end)].append((ccre_chr, ccre_start, ccre_end, ref_genome))

    return ccres


def associate_ccres(closest_ccre_filename, sources: list[CcreSource], ref_genome, accession_ids):
    source_ccres = source_ccre_locs(closest_ccre_filename, ref_genome)
    new_ccres = StringIO()
    ccre_associations = StringIO()
    found = 0
    missing = 0
    with FeatureIds() as feature_ids:
        for source in sources:
            ccres = source_ccres[(source.chrom_name, source.test_location.lower, source.test_location.upper)]
            if len(ccres) > 0:
                found += 1
                for ccre_id in get_ccres(ccres).all():
                    ccre_associations.write(f"{source._id}\t{ccre_id}\n")
            else:
                missing += 1
                feature_id = feature_ids.next_id()
                location = source.new_location if source.new_location is not None else source.test_location
                source_id = source._new_id if source._new_id is not None else source._id
                new_ccres.write(
                    f"{feature_id}\t{accession_ids.incr(AccessionType.CCRE)}\t{source.cell_line}\t{source.chrom_name}\t{source.closest_gene_id}\t{source.closest_gene_distance}\t{source.closest_gene_name}\t{source.closest_gene_ensembl_id}\t{location}\t{source.ref_genome}\t{source.ref_genome_patch}\t{json.dumps({'pseudo': True})}\t{DNAFeatureType.CCRE}\t{source.source_file_id}\t{source.experiment_accession_id}\tfalse\ttrue\n"
                )
                ccre_associations.write(f"{source_id}\t{feature_id}\n")
    save_ccres(new_ccres)
    save_associations(ccre_associations)
    print(f"Found: {found}")
    print(f"Missing: {missing}")
