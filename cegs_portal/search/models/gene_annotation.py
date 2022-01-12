from django.contrib.postgres.fields import IntegerRangeField
from django.db import models

from cegs_portal.search.models.features import Feature


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

    def __str__(self):
        first_field = f"{self.id_attr}: " if self.id_attr is not None else ""
        patch = f"p{self.ref_genome_patch}" if self.ref_genome_patch is not None else ""
        return f"{self.gene_name}: {first_field} {self.chrom_name}:{self.location.lower} - {self.location.upper} {self.strand} {self.ref_genome}{patch}: ({self.annotation_type})"  # noqa: E501
