from django.contrib.postgres.fields import ArrayField, IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models


class VariantLocation(models.Model):
    assembly = models.CharField(max_length=20)
    chromosome_name = models.CharField(max_length=10)
    location = IntegerRangeField()


class Variant(models.Model):
    class Meta:
        indexes = [GistIndex(fields=["location"], name="search_variant_location_index")]

    chromosome_name = models.CharField(max_length=10)
    assembly = models.CharField(max_length=20)
    location = IntegerRangeField()
    all_locations = models.ManyToManyField(VariantLocation)
    variant_id = ArrayField(models.CharField(max_length=30))
    reference_base = models.CharField(max_length=100)
    alternative_bases = ArrayField(models.CharField(max_length=30), null=True)
    SNP = "SNP"
    ENRICHED = "enriched"
    NON_SIGNIFICANT = "non_sig"
    BOTH = "both"
    KIND_CHOICES = [
        (SNP, "depleted"),
        (ENRICHED, "enriched"),
        (BOTH, "both"),
        (NON_SIGNIFICANT, "non_sig"),
    ]
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default=SNP)


class VCFFile(models.Model):
    header = models.JSONField(default=dict)
    sample_names = ArrayField(models.CharField(max_length=30), default=list)
    deleted = models.BooleanField(default=False)


class Subject(models.Model):
    subject_id = models.CharField(max_length=512, primary_key=True)
    source = models.CharField(max_length=512)
    files = models.ManyToManyField(VCFFile)


class VCFEntry(models.Model):
    file = models.ForeignKey(VCFFile, on_delete=models.CASCADE, related_name="entries")
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, related_name="entries", null=True)
    quality = models.FloatField(null=True)
    filters = ArrayField(models.CharField(max_length=30), default=list, null=True)
    info = models.CharField(max_length=50, null=True)
    sample_format = models.CharField(max_length=50, null=True)
    sample_data = ArrayField(models.CharField(max_length=50), default=list, null=True)
    genotypes = ArrayField(models.CharField(max_length=10), default=list, null=True)  # GT field in sample data
    heterozygosities = ArrayField(models.BooleanField(default=True), default=list, null=True)  # derived from genotype
    phased = ArrayField(models.BooleanField(default=True), default=list, null=True)  # derived from genotype
    allele_frequency = models.FloatField()  # AF in INFO column
    read_depth = models.IntegerField()  # DP field in sample data OR DP in INFO column
    mappability = models.FloatField()  # MQ field in sample data OR MQ in INFO column
    deleted = models.BooleanField(default=False)
