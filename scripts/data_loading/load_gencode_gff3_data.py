from urllib.parse import unquote

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNAFeature,
    DNAFeatureType,
    GencodeAnnotation,
    GencodeRegion,
)
from utils import timer

from .utils import AccessionIds, AccessionType

# Attributes that are saved in the annotation table rather than the attribute tabale
ANNOTATION_VALUE_ATTRIBUTES = {"ID", "gene_name", "gene_type", "level"}

ANNOTATION_BUFFER_SIZE = 5_000


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
@timer("Saving annotations", level=2, unit="s")
def bulk_annotation_save(genome_annotations: list[GencodeAnnotation]):
    GencodeAnnotation.objects.bulk_create(genome_annotations, batch_size=1000)


@timer("Loading annotations", level=1)
def load_genome_annotations(genome_annotations, ref_genome, ref_genome_patch, version):
    line_count = 0
    annotations: list[GencodeAnnotation] = []
    region = None
    for line in genome_annotations:
        line_count += 1
        if line_count % ANNOTATION_BUFFER_SIZE == 0:
            print(f"line count: {line_count}")

        if line.startswith("##sequence-region"):
            _, chrom_name, start, end = line.split(" ")
            # Adjust start/end to use 0-based indexing
            start = int(start) - 1
            end = int(end)
            region = GencodeRegion(chrom_name=chrom_name, base_range=NumericRange(start, end))
            region.save()
            continue

        if line.startswith("#"):
            continue

        fields = line.split("\t")
        seqid, _source, annotation_type, start, end, score_str, strand, phase_str, attrs = map(unquote, fields)
        attr_list = attrs.split(";")
        attr_dict = {}
        for attr in attr_list:
            attr_name, value = attr.split("=")
            attr_dict[attr_name.strip()] = value.strip()

        # The assumption is that all items with the same ID are on continguous lines
        phase = int(phase_str) if phase_str is not None and phase_str != "." else None
        score = float(score_str) if score_str is not None and score_str != "." else None

        # If there is a new annotation
        # Write the buffer to the database
        if len(annotations) % ANNOTATION_BUFFER_SIZE == 0:
            bulk_annotation_save(annotations)
            annotations = []
        # Create a new annotation

        annotation = GencodeAnnotation(
            chrom_name=seqid,
            location=NumericRange(int(start), int(end), "[]"),
            strand=strand,
            score=score,
            phase=phase,
            annotation_type=annotation_type,
            id_attr=attr_dict["ID"],
            ref_genome=ref_genome,
            ref_genome_patch=ref_genome_patch,
            gene_name=attr_dict["gene_name"],
            gene_type=attr_dict["gene_type"],
            level=int(attr_dict["level"]),
            region=region,
            version=version,
        )

        for v in ANNOTATION_VALUE_ATTRIBUTES:
            del attr_dict[v]

        annotation.attributes = attr_dict

        annotations.append(annotation)

    bulk_annotation_save(annotations)


def bulk_feature_save(assemblies, parent_ids=[]):
    with transaction.atomic():
        if len(parent_ids) > 0:
            parents = DNAFeature.objects.filter(ensembl_id__in=parent_ids)
            parents_dict = {p.ensembl_id: p for p in parents.all()}
            for a, pid in zip(assemblies, parent_ids):
                a.parent = parents_dict[pid]
        DNAFeature.objects.bulk_create(assemblies)


@timer("Creating Genes", level=1)
def create_genes(accession_ids, ref_genome, ref_genome_patch):
    gene_annotations = GencodeAnnotation.objects.filter(
        annotation_type="gene", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch
    )

    assembly_buffer = []
    for annotation in gene_annotations.iterator():
        if len(assembly_buffer) == ANNOTATION_BUFFER_SIZE:
            bulk_feature_save(assembly_buffer)
            assembly_buffer = []

        ensembl_id = None
        ids = {}
        if value := annotation.attributes.get("gene_id", False):
            ids["ensembl"] = value
            ensembl_id = value.split(".")[0]

        if value := annotation.attributes.get("hgnc_id", False):
            ids["hgnc"] = value

        if value := annotation.attributes.get("havana_gene", False):
            ids["havana"] = value

        assembly = DNAFeature(
            accession_id=accession_ids.incr(AccessionType.GENE),
            chrom_name=annotation.chrom_name,
            ids=ids,
            location=annotation.location,
            name=annotation.gene_name,
            strand=annotation.strand,
            ref_genome=annotation.ref_genome,
            ref_genome_patch=annotation.ref_genome_patch,
            feature_type=DNAFeatureType.GENE,
            feature_subtype=annotation.gene_type,
            ensembl_id=ensembl_id,
        )
        assembly_buffer.append(assembly)

    bulk_feature_save(assembly_buffer)


@timer("Creating Transcripts", level=1)
def create_transcripts(accession_ids, ref_genome, ref_genome_patch):
    tx_annotations = GencodeAnnotation.objects.filter(
        annotation_type="transcript", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch
    )

    assembly_buffer = []
    parent_ids = []
    for annotation in tx_annotations.iterator():
        if len(assembly_buffer) == ANNOTATION_BUFFER_SIZE:
            bulk_feature_save(assembly_buffer, parent_ids)
            assembly_buffer = []
            parent_ids = []

        ensembl_id = None
        ids = {}
        if value := annotation.attributes.get("transcript_id", False):
            ids["ensembl"] = value
            ensembl_id = value.split(".")[0]

        if value := annotation.attributes.get("havana_transcript", False):
            ids["havana"] = value

        parent_ids.append(annotation.attributes["gene_id"].split(".")[0])
        assembly = DNAFeature(
            accession_id=accession_ids.incr(AccessionType.TRANSCRIPT),
            chrom_name=annotation.chrom_name,
            ids=ids,
            location=annotation.location,
            name=annotation.attributes["transcript_name"],
            strand=annotation.strand,
            ref_genome=annotation.ref_genome,
            ref_genome_patch=annotation.ref_genome_patch,
            ensembl_id=ensembl_id,
            feature_type=DNAFeatureType.TRANSCRIPT,
            feature_subtype=annotation.attributes["transcript_type"],
        )
        assembly_buffer.append(assembly)

    bulk_feature_save(assembly_buffer, parent_ids)


@timer("Creating Exons", level=1)
def create_exons(accession_ids, ref_genome, ref_genome_patch):
    exon_annotations = GencodeAnnotation.objects.filter(
        annotation_type="exon", ref_genome=ref_genome, ref_genome_patch=ref_genome_patch
    )

    assembly_buffer = []
    parent_ids = []
    for annotation in exon_annotations.iterator():
        if len(assembly_buffer) == ANNOTATION_BUFFER_SIZE:
            bulk_feature_save(assembly_buffer, parent_ids)
            assembly_buffer = []
            parent_ids = []

        ids = {}
        exon_id = annotation.id_attr
        if value := annotation.attributes.get("exon_id", False):
            ids["ensembl"] = value
            exon_id = value

        parent_ids.append(annotation.attributes["transcript_id"].split(".")[0])
        assembly = DNAFeature(
            accession_id=accession_ids.incr(AccessionType.EXON),
            chrom_name=annotation.chrom_name,
            ids=ids,
            location=annotation.location,
            strand=annotation.strand,
            ref_genome=annotation.ref_genome,
            ref_genome_patch=annotation.ref_genome_patch,
            feature_type=DNAFeatureType.EXON,
            ensembl_id=exon_id,
            misc={"number": int(annotation.attributes["exon_number"]), "gencode_id": annotation.id_attr},
        )
        assembly_buffer.append(assembly)

    bulk_feature_save(assembly_buffer, parent_ids)


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
def run(annotation_filename: str, accession_file: str, ref_genome: str, ref_genome_patch: str, version: str):
    check_filename(annotation_filename)
    check_genome(ref_genome, ref_genome_patch)

    # Only run unload_genome_annotations if you want to delete all the gencode data in the db.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_genome_annotations() uncommented is not, strictly, idempotent.
    # unload_genome_annotations(ref_genome, ref_genome_patch)

    with open(annotation_filename, "r") as annotation_file:
        load_genome_annotations(annotation_file, ref_genome, ref_genome_patch, version)

    with AccessionIds(accession_file) as accession_ids:
        create_genes(accession_ids, ref_genome, ref_genome_patch)
        create_transcripts(accession_ids, ref_genome, ref_genome_patch)
        create_exons(accession_ids, ref_genome, ref_genome_patch)
