from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models

from cegs_portal.search.models.experiment import Experiment
from cegs_portal.search.models.gff3 import Gene
from cegs_portal.search.models.utils import ChromosomeLocation


class DNaseIHypersensitiveSite(models.Model):
    class Meta:
        indexes = [GistIndex(fields=["location"], name="search_dhs_location_index")]

    cell_line = models.CharField(max_length=50)
    chromosome_name = models.CharField(max_length=10)
    closest_gene = models.ForeignKey(Gene, null=True, on_delete=models.SET_NULL)
    closest_gene_distance = models.IntegerField()
    closest_gene_name = models.CharField(max_length=50)
    location = IntegerRangeField()
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10, null=True)
    strand = models.CharField(max_length=1, null=True, default=None)

    def __str__(self):
        return f"{self.chromosome_name} {self.location.lower}-{self.location.upper} ({self.cell_line})"

    @classmethod
    def search(self, terms):
        query = None
        for term in terms:
            if isinstance(term, ChromosomeLocation):
                if query is None:
                    query = DNaseIHypersensitiveSite.objects.filter(
                        chromosome_name=term.chromo, location__overlap=term.range
                    )
                else:
                    query = query | DNaseIHypersensitiveSite.objects.filter(
                        chromosome_name=term.chromo, location__overlap=term.range
                    )
        return query or []


class RegulatoryEffect(models.Model):
    DEPLETED = "depleted"
    ENRICHED = "enriched"
    NON_SIGNIFICANT = "non_sig"
    BOTH = "both"
    DIRECTION_CHOICES = [
        (DEPLETED, "depleted"),
        (ENRICHED, "enriched"),
        (BOTH, "both"),
        (NON_SIGNIFICANT, "non_sig"),
    ]
    direction = models.CharField(
        max_length=8,
        choices=DIRECTION_CHOICES,
        default=NON_SIGNIFICANT,
    )
    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    score = models.FloatField(null=True)
    significance = models.FloatField(null=True)  # p value, normalized to -log10
    sources = models.ManyToManyField(DNaseIHypersensitiveSite, related_name="regulatory_effects")
    targets = models.ManyToManyField(Gene, related_name="regulatory_effects")

    def __str__(self):
        return f"{self.direction}: {self.sources.count()} source(s) -> {self.score} on {self.targets.count()} target(s)"
