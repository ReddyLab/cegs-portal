import csv
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from os import SEEK_SET
from typing import Optional

from django.db import connection, transaction
from django.db.models import F, Func
from psycopg2.extras import NumericRange

from cegs_portal.search.models import AccessionType, DNAFeature, DNAFeatureType
from scripts.data_loading.db import (
    bulk_feature_save,
    ccre_associate_entry,
    feature_entry,
)

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
    genome_assembly: str
    experiment_accession_id: str
    genome_assembly_patch: str = "0"
    _new_id: Optional[int] = None
    new_location: Optional[NumericRange] = None
    feature_type: DNAFeatureType = DNAFeatureType.CCRE
    misc: dict = field(default_factory=lambda: {"pseudo": True})


def save_associations(associations):
    associations.seek(0, SEEK_SET)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.copy_from(
            associations, "search_dnafeature_associated_ccres", columns=("from_dnafeature_id", "to_dnafeature_id")
        )


def get_ccres(genome_assembly) -> list[tuple[int, str, NumericRange]]:
    if genome_assembly not in ["hg19", "hg38"]:
        raise ValueError("Please enter either hg19 or hg38 for the assembly")

    return (
        DNAFeature.objects.filter(feature_type="DNAFeatureType.CCRE", ref_genome=genome_assembly)
        .order_by("chrom_name", Func(F("location"), function="lower"), Func(F("location"), function="upper"))
        .values_list("id", "chrom_name", "location")
        .all()
    )


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
                    ccre_associations.write(ccre_associate_entry(source._id, ccre_id))
            else:
                missing += 1
                feature_id = feature_ids.next_id()
                location = source.new_location if source.new_location is not None else source.test_location
                new_ccres.write(
                    feature_entry(
                        id_=feature_id,
                        accession_id=accession_ids.incr(AccessionType.CCRE),
                        cell_line=source.cell_line,
                        chrom_name=source.chrom_name,
                        closest_gene_id=source.closest_gene_id,
                        closest_gene_distance=source.closest_gene_distance,
                        closest_gene_name=source.closest_gene_name,
                        closest_gene_ensembl_id=source.closest_gene_ensembl_id,
                        location=location,
                        genome_assembly=source.ref_genome,
                        genome_assembly_patch=source.ref_genome_patch,
                        misc={"pseudo": True},
                        feature_type=DNAFeatureType.CCRE,
                        source_file_id=source.source_file_id,
                        experiment_accession_id=source.experiment_accession_id,
                    )
                )

                source_id = source._new_id if source._new_id is not None else source._id
                ccre_associations.write(ccre_associate_entry(source_id, feature_id))
    bulk_feature_save(new_ccres)
    save_associations(ccre_associations)
    print(f"Found: {found}")
    print(f"Missing: {missing}")
