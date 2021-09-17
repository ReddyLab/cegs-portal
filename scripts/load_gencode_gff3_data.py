from urllib.parse import unquote

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    Exon,
    ExonAssembly,
    GencodeGFF3Annotation,
    GencodeGFF3Region,
    Gene,
    GeneAssembly,
    Transcript,
    TranscriptAssembly,
)
from utils import timer

# Attributes that are saved in the annotation table rather than the attribute tabale
ANNOTATION_VALUE_ATTRIBUTES = {"ID", "gene_name", "gene_type", "level"}

ANNOTATION_BUFFER_SIZE = 50_000


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
@timer("Saving annotations", level=1, unit="s")
def bulk_annotation_save(genome_annotations):
    GencodeGFF3Annotation.objects.bulk_create(genome_annotations, batch_size=500)


@timer("Loading annotations")
def load_genome_annotations(genome_annotations, ref_genome, ref_genome_patch):
    line_count = 0
    annotations = []
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
            region = GencodeGFF3Region(chrom_name=chrom_name, base_range=NumericRange(start, end))
            region.save()
            continue

        if line.startswith("#"):
            continue

        fields = line.split("\t")
        seqid, _source, annotation_type, start, end, score, strand, phase, attrs = map(unquote, fields)
        attr_list = attrs.split(";")
        attr_dict = {}
        for attr in attr_list:
            attr_name, value = attr.split("=")
            attr_dict[attr_name.strip()] = value.strip()

        # The assumption is that all items with the same ID are on continguous lines
        phase = int(phase) if phase is not None and phase != "." else None
        score = float(score) if score is not None and score != "." else None

        # If there is a new annotation
        # Write the buffer to the database
        if len(annotations) % ANNOTATION_BUFFER_SIZE == 0:
            bulk_annotation_save(annotations)
            annotations = []
        # Create a new annotation

        annotation = GencodeGFF3Annotation(
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
        )

        for v in ANNOTATION_VALUE_ATTRIBUTES:
            del attr_dict[v]

        annotation.attributes = attr_dict

        annotations.append(annotation)

    bulk_annotation_save(annotations)


@timer("Creating Genes")
def create_genes():
    gene_annotations = GencodeGFF3Annotation.objects.filter(annotation_type="gene", gene_id=None)

    print("Creating Genes")
    for annotation in gene_annotations:

        # UPDATE public.search_gencodegff3annotation as a
        # SET gene_id = g.id
        # FROM public.search_gene AS g
        # WHERE starts_with(reverse(a.id_attr), 'Y_RAP_') and g.ensembl_id = split_part(a.id_attr, '.', 1);
        gene_id = annotation.id_attr
        if gene_id.endswith("_PAR_Y"):
            # These genes are from the Pseudoautosomal region of the Y chromosome and
            # have already been defined as part of the X chromosome.
            try:
                gene = Gene.objects.get(ensembl_id=gene_id.split(".")[0])
            except ObjectDoesNotExist:
                continue
            else:
                with transaction.atomic():
                    annotation.gene = gene
                    annotation.save()
                    continue

        ensembl_id = None
        ids = {}
        if value := annotation.attributes.get("gene_id", False):
            ids["ensembl"] = value
            ensembl_id = value.split(".")[0]

        if value := annotation.attributes.get("hgnc_id", False):
            ids["hgnc"] = value

        if value := annotation.attributes.get("havana_gene", False):
            ids["havana"] = value

        with transaction.atomic():
            assembly = GeneAssembly(
                chrom_name=annotation.chrom_name,
                ids=ids,
                location=annotation.location,
                name=annotation.gene_name,
                strand=annotation.strand,
                ref_genome=annotation.ref_genome,
                ref_genome_patch=annotation.ref_genome_patch,
            )

            try:
                gene = Gene.objects.get(ensembl_id=ensembl_id)
            except ObjectDoesNotExist:
                gene = Gene(gene_type=annotation.gene_type, ensembl_id=ensembl_id)
                gene.save()

                # The gene already exists, so just update it with a new assembly location
                # and add it to the annotation

            assembly.gene = gene
            assembly.save()
            gene.assemblies.add(assembly)


@timer("Creating Transcripts")
def create_transcripts():
    print("Creating Transcripts")
    tx_annotations = GencodeGFF3Annotation.objects.filter(annotation_type="transcript", transcript_id=None)

    gene_id = None
    for annotation in tx_annotations:
        transcript_id = annotation.id_attr
        if transcript_id.endswith("_PAR_Y"):
            # These transcripts are from the Pseudoautosomal region of the Y chromosome and
            # have already been defined as part of the X chromosome.
            try:
                transcript = Transcript.objects.get(ensembl_id=transcript_id.split(".")[0])
            except ObjectDoesNotExist:
                continue
            else:
                with transaction.atomic():
                    annotation.transcript = transcript
                    annotation.save()
                    continue

        ensembl_id = None
        ids = {}
        if value := annotation.attributes.get("transcript_id", False):
            ids["ensembl"] = value
            ensembl_id = value.split(".")[0]

        if value := annotation.attributes.get("havana_transcript", False):
            ids["havana"] = value

        with transaction.atomic():
            assembly = TranscriptAssembly(
                chrom_name=annotation.chrom_name,
                ids=ids,
                location=annotation.location,
                name=annotation.attributes["transcript_name"],
                strand=annotation.strand,
                ref_genome=annotation.ref_genome,
                ref_genome_patch=annotation.ref_genome_patch,
            )

            try:
                transcript = Transcript.objects.get(ensembl_id=ensembl_id)
            except ObjectDoesNotExist:
                temp_gene_id = annotation.attributes["gene_id"].split(".")[0]
                if gene_id != temp_gene_id:
                    gene_id = temp_gene_id
                gene = Gene.objects.get(ensembl_id=gene_id)
                transcript = Transcript(
                    ensembl_id=ensembl_id,
                    gene=gene,
                    transcript_type=annotation.attributes["transcript_type"],
                )
                transcript.save()

            assembly.transcript = transcript
            assembly.save()
            transcript.assemblies.add(assembly)


@timer("Creating Exons")
def create_exons():
    print("Creating Exons")
    exon_annotations = GencodeGFF3Annotation.objects.filter(annotation_type="exon").filter(exon=None)

    gene_id = None
    transcript_id = None
    for annotation in exon_annotations:
        exon_id = annotation.id_attr
        if exon_id.count("_PAR_Y") > 0:
            # These exons are from the Pseudoautosomal region of the Y chromosome and
            # have already been defined as part of the X chromosome.
            continue

        ids = {}
        if value := annotation.attributes.get("exon_id", False):
            ids["ensembl"] = value

        with transaction.atomic():
            assembly = ExonAssembly(
                chrom_name=annotation.chrom_name,
                ids=ids,
                location=annotation.location,
                strand=annotation.strand,
                ref_genome=annotation.ref_genome,
                ref_genome_patch=annotation.ref_genome_patch,
            )

            try:
                exon = Exon.objects.get(ensembl_id=exon_id)
            except ObjectDoesNotExist:
                temp_gene_id = annotation.attributes["gene_id"].split(".")[0]
                if gene_id != temp_gene_id:
                    gene_id = temp_gene_id
                gene = Gene.objects.get(ensembl_id=gene_id)

                temp_transcript_id = annotation.attributes["transcript_id"].split(".")[0]
                if transcript_id != temp_transcript_id:
                    transcript_id = temp_transcript_id
                transcript = Transcript.objects.get(ensembl_id=transcript_id)

                exon = Exon(
                    gene=gene,
                    ensembl_id=ids["ensembl"],
                    number=annotation.attributes["exon_number"],
                    transcript=transcript,
                )
                exon.save()

            assembly.exon = exon
            assembly.save()
            exon.assemblies.add(assembly)


def unload_genome_annotations():
    GencodeGFF3Region.objects.all().delete()
    GencodeGFF3Annotation.objects.all().delete()
    Gene.objects.all().delete()
    GeneAssembly.objects.all().delete()
    Transcript.objects.all().delete()
    TranscriptAssembly.objects.all().delete()
    Exon.objects.all().delete()
    ExonAssembly.objects.all().delete()


def check_filename(annotation_filename: str):
    if len(annotation_filename) == 0:
        raise ValueError(f"annotation filename '{annotation_filename}' must not be blank")


def check_genome(ref_genome: str, ref_genome_patch: str):
    if len(ref_genome) == 0:
        raise ValueError(f"reference genome '{ref_genome}'must not be blank")

    if not ((ref_genome_patch.isascii() and ref_genome_patch.isdigit()) or len(ref_genome_patch) == 0):
        raise ValueError(f"reference genome patch '{ref_genome_patch}' must be either blank or a series of digits")


def run(annotation_filename: str, ref_genome: str, ref_genome_patch: str):
    check_filename(annotation_filename)
    check_genome(ref_genome, ref_genome_patch)

    # Only run unload_genome_annotations if you want to delete all the gencode data in the db.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_genome_annotations() uncommented is not, strictly, idempotent.
    # unload_genome_annotations()

    with open(annotation_filename, "r") as annotation_file:
        load_genome_annotations(annotation_file, ref_genome, ref_genome_patch)

    create_genes()
    create_transcripts()
    create_exons()
