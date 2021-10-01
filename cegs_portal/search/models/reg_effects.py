from enum import Enum

from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.db.models import Q

from cegs_portal.search.models.experiment import Experiment
from cegs_portal.search.models.file import File
from cegs_portal.search.models.gff3 import Gene, GeneAssembly
from cegs_portal.search.models.utils import QueryToken


class DNaseIHypersensitiveSite(models.Model):
    class Meta:
        indexes = [GistIndex(fields=["location"], name="search_dhs_location_index")]

    cell_line = models.CharField(max_length=50, null=True)
    chromosome_name = models.CharField(max_length=10)
    closest_gene = models.ForeignKey(Gene, null=True, on_delete=models.SET_NULL)
    closest_gene_assembly = models.ForeignKey(GeneAssembly, null=True, on_delete=models.SET_NULL)
    closest_gene_distance = models.IntegerField()
    closest_gene_name = models.CharField(max_length=50)
    location = IntegerRangeField()
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10, null=True)
    screen_accession_id = models.CharField(max_length=20, null=True)
    source = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.chromosome_name} {self.location.lower}-{self.location.upper} ({self.cell_line})"

    @classmethod
    def search(cls, terms):
        q = None
        for term, value in terms:
            if term == QueryToken.LOCATION:
                if q is None:
                    q = Q(chromosome_name=value.chromo, location__overlap=value.range)
                else:
                    q = q | Q(chromosome_name=value.chromo, location__overlap=value.range)
        return cls.objects.filter(q).select_related("closest_gene") if q is not None else []


class EffectDirectionType(Enum):
    DEPLETED = "depleted"
    ENRICHED = "enriched"
    NON_SIGNIFICANT = "non_sig"
    BOTH = "both"


class RegulatoryEffect(models.Model):
    DIRECTION_CHOICES = [
        (EffectDirectionType.DEPLETED, "depleted"),  # significance < 0.01, effect size -
        (EffectDirectionType.ENRICHED, "enriched"),  # significance < 0.01, effect size +
        (EffectDirectionType.BOTH, "both"),
        (EffectDirectionType.NON_SIGNIFICANT, "non_sig"),  # significance >= 0.01 or value = 0
    ]
    direction = models.CharField(
        max_length=8,
        choices=DIRECTION_CHOICES,
        default=EffectDirectionType.NON_SIGNIFICANT,
    )
    experiment = models.ForeignKey(Experiment, null=True, on_delete=models.SET_NULL)
    effect_size = models.FloatField(null=True)  # log2 fold changes
    significance = models.FloatField(null=True)  # an adjusted p value
    raw_p_value = models.FloatField(null=True)  # p value, scaled with -log10
    sources = models.ManyToManyField(DNaseIHypersensitiveSite, related_name="regulatory_effects")
    targets = models.ManyToManyField(Gene, related_name="regulatory_effects")
    target_assemblies = models.ManyToManyField(GeneAssembly, related_name="regulatory_effects")

    def __str__(self):
        return f"{self.direction}: {self.sources.count()} source(s) -> {self.effect_size} on {self.targets.count()} target(s)"  # noqa: E501
