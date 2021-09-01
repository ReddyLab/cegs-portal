from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.db.models import Q

from cegs_portal.search.models.utils import QueryToken
from cegs_portal.search.models.validators import validate_gene_ids


class GeneAssembly(models.Model):
    class Meta:
        indexes = [models.Index(fields=["name"], name="search_geneassembly_name_index")]

    chrom_name = models.CharField(max_length=10)
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    name = models.CharField(max_length=50)
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)

    @classmethod
    def search(cls, terms):
        q = None
        for term, value in terms:
            if term == QueryToken.LOCATION:
                if q is None:
                    q = Q(chrom_name=value.chromo, location__overlap=value.range)
                else:
                    q = q | Q(chrom_name=value.chromo, location__overlap=value.range)
        print(q)
        return cls.objects.filter(q) if q is not None else []


class TranscriptAssembly(models.Model):
    chrom_name = models.CharField(max_length=10)
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    name = models.CharField(max_length=80)
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)


class ExonAssembly(models.Model):
    chrom_name = models.CharField(max_length=10)
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)


class Gene(models.Model):
    class Meta:
        indexes = [models.Index(fields=["ensembl_id"], name="search_gene_ensembl_id_index")]

    assemblies = models.ManyToManyField(GeneAssembly, related_name="gene")
    ensembl_id = models.CharField(max_length=50, unique=True, default="No ID")
    gene_type = models.CharField(max_length=50)

    @classmethod
    def search(cls, terms):
        q = None
        for term, value in terms:
            if term == QueryToken.ENSEMBL_ID:
                if q is None:
                    q = Q(ensembl_id=value)
                else:
                    q = q | Q(ensembl_id=value)
        return cls.objects.filter(q) if q is not None else []


class Transcript(models.Model):
    assemblies = models.ManyToManyField(TranscriptAssembly, related_name="transcript")
    ensembl_id = models.CharField(max_length=50, unique=True, default="No ID")
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    transcript_type = models.CharField(max_length=50)


class Exon(models.Model):
    assemblies = models.ManyToManyField(ExonAssembly, related_name="exon")
    ensembl_id = models.CharField(max_length=50, unique=True, default="No ID")
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    number = models.IntegerField()
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE)


class GencodeGFF3Region(models.Model):
    chrom_name = models.CharField(max_length=10)
    base_range = IntegerRangeField()  # 0-indexed, half-closed

    def __str__(self):
        return f"{self.chrom_name} {self.base_range.lower} {self.base_range.upper}"


class GencodeGFF3Annotation(models.Model):
    chrom_name = models.CharField(max_length=10)
    annotation_type = models.CharField(max_length=100)
    id_attr = models.CharField(max_length=50)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)
    gene_name = models.CharField(max_length=50)
    gene_type = models.CharField(max_length=50)
    level = models.IntegerField()
    region = models.ForeignKey(GencodeGFF3Region, on_delete=models.SET_NULL, null=True)
    parent_annotation = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="parent"
    )
    gene = models.ForeignKey(
        Gene,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="annotation",
    )
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="annotation",
    )
    exon = models.ForeignKey(
        Exon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="annotation",
    )

    def save(self, *args, **kwargs):
        if self.parent_annotation is not None and self.parent_annotation_id is None:
            self.parent_annotation_id = self.parent_annotation.id
        super(GencodeGFF3Annotation, self).save(*args, **kwargs)

    def __str__(self):
        first_field = f"{self.id_attr}: " if self.id_attr is not None else ""
        patch = f"p{self.ref_genome_patch}" if self.ref_genome_patch is not None else ""
        return f"{self.gene_name}: {first_field}{self.ref_genome}{patch}: ({self.annotation_type})"


class GencodeGFF3Entry(models.Model):
    class Meta:
        indexes = [GistIndex(fields=["location"], name="search_gcgentry_location_index")]

    seqid = models.CharField(max_length=500)
    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    strand = models.CharField(max_length=1)
    score = models.FloatField(null=True)
    phase = models.IntegerField(null=True)
    annotation = models.ForeignKey(GencodeGFF3Annotation, on_delete=models.CASCADE, related_name="entries")

    def __str__(self):
        return f"{self.annotation.id_attr}: {self.location.lower} - {self.location.upper}:{self.strand}"


class GencodeGFF3Attribute(models.Model):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=500)
    entry = models.ForeignKey(
        GencodeGFF3Entry,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="attributes",
    )
    annotation = models.ForeignKey(
        GencodeGFF3Annotation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="attributes",
    )

    def __str__(self):
        return f"{self.name}={self.value}"
