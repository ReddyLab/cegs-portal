from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.db.models import Q

from cegs_portal.search.models.utils import QueryToken
from cegs_portal.search.models.validators import validate_gene_ids


class FeatureAssembly(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["name"], name="sfa_name_index"),
            models.Index(fields=["chrom_name"], name="sfa_chrom_name_index"),
            GistIndex(fields=["location"], name="sfa_loc_index"),
        ]

    chrom_name = models.CharField(max_length=10)
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    name = models.CharField(max_length=50)
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)
    feature = models.ForeignKey("Feature", on_delete=models.CASCADE, related_name="assemblies")

    def __str__(self):
        return f"{self.name} -- {self.chrom_name}:{self.location.lower}-{self.location.upper} ({self.ref_genome})"

    @classmethod
    def search(cls, terms):
        q = None
        for term, value in terms:
            if term == QueryToken.LOCATION:
                if q is None:
                    q = Q(chrom_name=value.chromo, location__overlap=value.range)
                else:
                    q = q | Q(chrom_name=value.chromo, location__overlap=value.range)
        return cls.objects.filter(q).select_related("feature") if q is not None else []


class Feature(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["ensembl_id"], name="sf_ensembl_id_index"),
            models.Index(fields=["feature_type"], name="sf_feature_type_index"),
        ]

    ensembl_id = models.CharField(max_length=50, unique=True, default="No ID")
    feature_type = models.CharField(max_length=50)  # gene, tanscript, etc.
    # gene_type or transcript_type from gencodeannotation.attributes
    feature_subtype = models.CharField(max_length=50, null=True)
    misc = models.JSONField(null=True)  # exon number, for instance
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, related_name="children")

    def __str__(self):
        return f"{self.ensembl_id}: {self.feature_type}"

    @classmethod
    def search(cls, terms):
        q = None
        for term, value in terms:
            if term == QueryToken.ENSEMBL_ID:
                if q is None:
                    q = Q(ensembl_id=value)
                else:
                    q = q | Q(ensembl_id=value)
        return cls.objects.filter(q).prefetch_related("assemblies") if q is not None else []


class GeneAssembly(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["name"], name="search_geneassembly_name_index"),
            GistIndex(fields=["location"], name="search_geneassembly_loc_index"),
        ]

    chrom_name = models.CharField(max_length=10)
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    name = models.CharField(max_length=50)
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)

    # Creates a "one-to-many" relationship pair with Gene, which has a ManyToMany field for GeneAssemblys
    gene = models.ForeignKey("Gene", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} -- {self.chrom_name}:{self.location.lower}-{self.location.upper} ({self.ref_genome})"

    @classmethod
    def search(cls, terms):
        q = None
        for term, value in terms:
            if term == QueryToken.LOCATION:
                if q is None:
                    q = Q(chrom_name=value.chromo, location__overlap=value.range)
                else:
                    q = q | Q(chrom_name=value.chromo, location__overlap=value.range)
        return cls.objects.filter(q).select_related("gene") if q is not None else []


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

    # Creates a "one-to-many" relationship pair with Transcript, which has a ManyToMany field for TranscriptAssemblys
    transcript = models.ForeignKey("Transcript", on_delete=models.CASCADE)


class ExonAssembly(models.Model):
    chrom_name = models.CharField(max_length=10)
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)

    # Creates a "one-to-many" relationship pair with Exon, which has a ManyToMany field for ExonAssemblys
    exon = models.ForeignKey("Exon", on_delete=models.CASCADE)


class Gene(models.Model):
    class Meta:
        indexes = [models.Index(fields=["ensembl_id"], name="search_gene_ensembl_id_index")]

    # GeneAssemblys have an associated foreign key to create a one-to-many relationship
    assemblies = models.ManyToManyField(GeneAssembly, related_name="gene_set")
    ensembl_id = models.CharField(max_length=50, unique=True, default="No ID")
    gene_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.ensembl_id}: {self.gene_type}"

    @classmethod
    def search(cls, terms):
        q = None
        for term, value in terms:
            if term == QueryToken.ENSEMBL_ID:
                if q is None:
                    q = Q(ensembl_id=value)
                else:
                    q = q | Q(ensembl_id=value)
        return cls.objects.filter(q).prefetch_related("assemblies") if q is not None else []


class Transcript(models.Model):
    class Meta:
        indexes = [models.Index(fields=["ensembl_id"], name="search_tx_ensembl_id_index")]

    assemblies = models.ManyToManyField(TranscriptAssembly, related_name="transcript_set")
    ensembl_id = models.CharField(max_length=50, unique=True, default="No ID")
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    transcript_type = models.CharField(max_length=50)


class Exon(models.Model):
    class Meta:
        indexes = [models.Index(fields=["ensembl_id"], name="search_exon_ensembl_id_index")]

    assemblies = models.ManyToManyField(ExonAssembly, related_name="exon_set")
    ensembl_id = models.CharField(max_length=50, unique=False, default="No ID")
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    number = models.IntegerField()
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE)


class GencodeRegion(models.Model):
    chrom_name = models.CharField(max_length=10)
    base_range = IntegerRangeField()  # 0-indexed, half-closed

    def __str__(self):
        return f"{self.chrom_name} {self.base_range.lower} {self.base_range.upper}"


# Note that the following annotation_types might have multiple entries for a single ID attribute:
# stop_codon, three_prime_UTR, start_codon, and five_prime_UTR.
class GencodeAnnotation(models.Model):
    class Meta:
        indexes = [models.Index(fields=["annotation_type"], name="search_gen_anno_type_index")]

    chrom_name = models.CharField(max_length=10)
    location = IntegerRangeField()
    strand = models.CharField(max_length=1)
    score = models.FloatField(null=True)
    phase = models.IntegerField(null=True)
    annotation_type = models.CharField(max_length=100)
    id_attr = models.CharField(max_length=50)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)
    gene_name = models.CharField(max_length=50)
    gene_type = models.CharField(max_length=50)
    level = models.IntegerField()
    region = models.ForeignKey(GencodeRegion, on_delete=models.SET_NULL, null=True)
    attributes = models.JSONField(null=True)

    feature = models.ForeignKey(
        Feature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="annotation",
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

    def __str__(self):
        first_field = f"{self.id_attr}: " if self.id_attr is not None else ""
        patch = f"p{self.ref_genome_patch}" if self.ref_genome_patch is not None else ""
        return f"{self.gene_name}: {first_field} {self.chrom_name}:{self.location.lower} - {self.location.upper} {self.strand} {self.ref_genome}{patch}: ({self.annotation_type})"  # noqa: E501
