import json
from io import SEEK_SET, StringIO
from urllib.parse import unquote

from django.db import connection, transaction
from psycopg.types.range import Int4Range

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    GencodeAnnotation,
    GencodeRegion,
)
from cegs_portal.utils.db_ids import FeatureIds
from utils import timer

from .db import bulk_feature_save, feature_entry

# Attributes that are saved in the annotation table rather than the attribute tabale
ANNOTATION_VALUE_ATTRIBUTES = {"ID", "gene_name", "gene_type", "level"}

ANNOTATION_BUFFER_SIZE = 100_000


#
# The following lines should work as expected when using postgres. See
# https://docs.djangoproject.com/en/4.0/ref/models/querysets/#bulk-create
#
#     If the model’s primary key is an AutoField, the primary key attribute can only
#     be retrieved on certain databases (currently PostgreSQL, MariaDB 10.5+, and
#     SQLite 3.35+). On other databases, it will not be set.
#
# So the objects won't need to be saved one-at-a-time like they are, which is slow.
#
# In postgres the objects automatically get their id's when bulk_created but
# objects that reference the bulk_created objects (i.e., with foreign keys) don't
# get their foreign keys updated. The for loops do that necessary updating.
def bulk_annotation_save(genome_annotations: StringIO):
    genome_annotations.seek(0, SEEK_SET)
    with transaction.atomic(), connection.cursor() as cursor:
        with cursor.copy(
            """COPY search_gencodeannotation (
                chrom_name,
                location,
                strand,
                score,
                phase,
                annotation_type,
                id_attr,
                ref_genome,
                ref_genome_patch,
                gene_name,
                gene_type,
                level,
                region_id,
                version,
                attributes,
            ) FROM STDIN"""
        ) as copy:
            copy.write(genome_annotations)


@timer("Loading annotations", level=1)
def load_genome_annotations(genome_annotations, ref_genome, ref_genome_patch, version):
    annotations: StringIO = StringIO()
    region = None
    for i, line in enumerate(genome_annotations, start=1):
        if line.startswith("##sequence-region"):
            _, chrom_name, start, end = line.split(" ")
            # Genocode values are 1-based, and probably closed
            # Adjust start/end to use 0-based indexing
            start = int(start) - 1
            end = int(end)
            region = GencodeRegion(chrom_name=chrom_name, base_range=Int4Range(start, end, "[)"))
            region.save()
            continue

        if line.startswith("#"):
            continue

        fields = line.split("\t")
        seqid, _source, annotation_type, start, end, score_str, strand, phase_str, attrs = map(unquote, fields)
        # Genocode values are 1-based, and probably closed
        # Adjust start/end to use 0-based indexing
        start = int(start) - 1
        end = int(end)
        attr_list = attrs.split(";")
        attr_dict = {}
        for attr in attr_list:
            attr_name, value = attr.split("=")
            attr_dict[attr_name.strip()] = value.strip()

        annotation_id = attr_dict["ID"]
        gene_name = attr_dict["gene_name"]
        gene_type = attr_dict["gene_type"]
        level = attr_dict["level"]

        for v in ANNOTATION_VALUE_ATTRIBUTES:
            del attr_dict[v]

        # The assumption is that all items with the same ID are on continguous lines
        # \N represents a "null" value to psycopg2
        phase = phase_str if phase_str is not None and phase_str != "." else "\\N"
        score = score_str if score_str is not None and score_str != "." else "\\N"

        # If there is a new annotation
        # Write the buffer to the database
        if i % ANNOTATION_BUFFER_SIZE == 0:
            bulk_annotation_save(annotations)
            annotations.close()
            annotations = StringIO()

        # Create a new annotation
        annotations.write(
            f"{seqid}\t[{start},{end})\t{strand}\t{score}\t{phase}\t{annotation_type}\t{annotation_id}\t{ref_genome}\t{ref_genome_patch}\t{gene_name}\t{gene_type}\t{level}\t{region.id}\t{version}\t{json.dumps(attr_dict)}\n"
        )

    bulk_annotation_save(annotations)
    annotations.close()


@timer("Creating Genes", level=1)
def create_genes(accession_ids, ref_genome, ref_genome_patch):
    gene_annotations = GencodeAnnotation.objects.filter(
        annotation_type="gene", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch
    ).values()

    assembly_buffer = StringIO()
    ensembl_ids = {}
    with FeatureIds() as feature_ids:
        for i, (feature_id, annotation) in enumerate(zip(feature_ids, gene_annotations.iterator()), start=1):
            if i % ANNOTATION_BUFFER_SIZE == 0:
                bulk_feature_save(assembly_buffer)
                assembly_buffer.close()
                assembly_buffer = StringIO()

            ensembl_id = None
            accession_id = accession_ids.incr(AccessionType.GENE)
            ids = {}
            if value := annotation["attributes"].get("gene_id", False):
                ids["ensembl"] = value
                ensembl_id = value.split(".")[0]
                ensembl_ids[ensembl_id] = (feature_id, accession_id)

            if value := annotation["attributes"].get("hgnc_id", False):
                ids["hgnc"] = value

            if value := annotation["attributes"].get("havana_gene", False):
                ids["havana"] = value

            assembly_buffer.write(
                feature_entry(
                    id_=feature_id,
                    accession_id=accession_id,
                    ids=ids,
                    ensembl_id=ensembl_id,
                    name=annotation["gene_name"],
                    chrom_name=annotation["chrom_name"],
                    location=annotation["location"],
                    strand=annotation["strand"],
                    genome_assembly=annotation["ref_genome"],
                    genome_assembly_patch=annotation["ref_genome_patch"],
                    feature_type=DNAFeatureType.GENE,
                    feature_subtype=annotation["gene_type"],
                )
            )

    bulk_feature_save(assembly_buffer)

    return ensembl_ids


@timer("Creating Transcripts", level=1)
def create_transcripts(accession_ids, gene_ensembl_ids, ref_genome, ref_genome_patch):
    tx_annotations = GencodeAnnotation.objects.filter(
        annotation_type="transcript", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch
    ).values()

    assembly_buffer = StringIO()
    ensembl_ids = {}
    with FeatureIds() as feature_ids:
        for i, (feature_id, annotation) in enumerate(zip(feature_ids, tx_annotations.iterator()), start=1):
            if i % ANNOTATION_BUFFER_SIZE == 0:
                bulk_feature_save(assembly_buffer)
                assembly_buffer.close()
                assembly_buffer = StringIO()

            ensembl_id = None
            accession_id = accession_ids.incr(AccessionType.TRANSCRIPT)

            ids = {}
            if value := annotation["attributes"].get("transcript_id", False):
                ids["ensembl"] = value
                ensembl_id = value.split(".")[0]
                ensembl_ids[ensembl_id] = (feature_id, accession_id)

            if value := annotation["attributes"].get("havana_transcript", False):
                ids["havana"] = value

            parent_id = annotation["attributes"]["gene_id"].split(".")[0]
            pid, p_a_id = gene_ensembl_ids[parent_id]
            assembly_buffer.write(
                feature_entry(
                    id_=feature_id,
                    accession_id=accession_id,
                    ids=ids,
                    ensembl_id=ensembl_id,
                    name=annotation["attributes"]["transcript_name"],
                    chrom_name=annotation["chrom_name"],
                    location=annotation["location"],
                    strand=annotation["strand"],
                    genome_assembly=annotation["ref_genome"],
                    genome_assembly_patch=annotation["ref_genome_patch"],
                    feature_type=DNAFeatureType.TRANSCRIPT,
                    feature_subtype=annotation["attributes"]["transcript_type"],
                    parent_id=pid,
                    parent_accession_id=p_a_id,
                )
            )

    bulk_feature_save(assembly_buffer)

    return ensembl_ids


@timer("Creating Exons", level=1)
def create_exons(accession_ids, tx_ensembl_ids, ref_genome, ref_genome_patch):
    exon_annotations = GencodeAnnotation.objects.filter(
        annotation_type="exon", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch
    ).values()

    assembly_buffer = StringIO()
    with FeatureIds() as feature_ids:
        for i, (feature_id, annotation) in enumerate(zip(feature_ids, exon_annotations.iterator())):
            if i % ANNOTATION_BUFFER_SIZE == 0:
                bulk_feature_save(assembly_buffer)
                assembly_buffer.close()
                assembly_buffer = StringIO()

            ids = {}
            exon_id = annotation["id_attr"]
            if value := annotation["attributes"].get("exon_id", False):
                ids["ensembl"] = value
                exon_id = value

            parent_id = annotation["attributes"]["transcript_id"].split(".")[0]
            pid, p_a_id = tx_ensembl_ids[parent_id]
            assembly_buffer.write(
                feature_entry(
                    id_=feature_id,
                    accession_id=accession_ids.incr(AccessionType.EXON),
                    ids=ids,
                    ensembl_id=exon_id,
                    chrom_name=annotation["chrom_name"],
                    location=annotation["location"],
                    strand=annotation["strand"],
                    genome_assembly=annotation["ref_genome"],
                    genome_assembly_patch=annotation["ref_genome_patch"],
                    feature_type=DNAFeatureType.EXON,
                    parent_id=pid,
                    parent_accession_id=p_a_id,
                    misc={"number": int(annotation["attributes"]["exon_number"]), "gencode_id": annotation["id_attr"]},
                )
            )

    bulk_feature_save(assembly_buffer)


@timer("Unloading Genome Annotations", level=1)
def unload_genome_annotations(ref_genome, ref_genome_patch):
    annotations = GencodeAnnotation.objects.filter(ref_genome=ref_genome, ref_genome_patch=ref_genome_patch)
    annotation_regions = annotations.values_list("region_id")
    GencodeRegion.objects.filter(id__in=annotation_regions).delete()
    annotations.delete()
    DNAFeature.objects.filter(
        feature_type__in=[DNAFeatureType.GENE, DNAFeatureType.EXON, DNAFeatureType.TRANSCRIPT],
        ref_genome=ref_genome,
        ref_genome_patch=ref_genome_patch,
    ).delete()


def check_filename(annotation_filename: str):
    if len(annotation_filename) == 0:
        raise ValueError(f"annotation filename '{annotation_filename}' must not be blank")


def check_genome(ref_genome: str, ref_genome_patch: str):
    if len(ref_genome) == 0:
        raise ValueError(f"reference genome '{ref_genome}'must not be blank")

    if not ((ref_genome_patch.isascii() and ref_genome_patch.isdigit()) or len(ref_genome_patch) == 0):
        raise ValueError(f"reference genome patch '{ref_genome_patch}' must be either blank or a series of digits")


@timer("Load Gencode Data")
def run(annotation_filename: str, ref_genome: str, ref_genome_patch: str, version: str):
    check_filename(annotation_filename)
    check_genome(ref_genome, ref_genome_patch)

    # Only run unload_genome_annotations if you want to delete all the gencode data in the db.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_genome_annotations() uncommented is not, strictly, idempotent.
    # unload_genome_annotations(ref_genome, ref_genome_patch)

    with open(annotation_filename, "r") as annotation_file:
        load_genome_annotations(annotation_file, ref_genome, ref_genome_patch, version)

    with AccessionIds(message=f"Gencode data for {ref_genome}.{ref_genome_patch}") as accession_ids:
        gene_ensembl_ids = create_genes(accession_ids, ref_genome, ref_genome_patch)
        transcript_ensembl_ids = create_transcripts(accession_ids, gene_ensembl_ids, ref_genome, ref_genome_patch)
        create_exons(accession_ids, transcript_ensembl_ids, ref_genome, ref_genome_patch)
