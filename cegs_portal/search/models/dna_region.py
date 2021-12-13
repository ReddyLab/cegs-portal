from typing import Optional

from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.db.models import Prefetch, Q

from cegs_portal.search.models.facets import FacetedModel
from cegs_portal.search.models.features import Feature, FeatureAssembly
from cegs_portal.search.models.file import File
from cegs_portal.search.models.searchable import Searchable
from cegs_portal.search.models.utils import ChromosomeLocation


class DNARegion(Searchable, FacetedModel):
    class Meta:
        indexes = [GistIndex(fields=["location"], name="search_region_location_index")]

    cell_line = models.CharField(max_length=50, null=True)
    chromosome_name = models.CharField(max_length=10)
    closest_gene = models.ForeignKey(Feature, null=True, on_delete=models.SET_NULL)
    closest_gene_assembly = models.ForeignKey(FeatureAssembly, null=True, on_delete=models.SET_NULL)
    closest_gene_distance = models.IntegerField()
    closest_gene_name = models.CharField(max_length=50)
    location = IntegerRangeField()
    misc = models.JSONField(null=True)  # screen_accession_id, for instance
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10, null=True)
    region_type = models.CharField(max_length=50, default="")
    source = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)
    strand = models.CharField(max_length=1, null=True)

    def __str__(self):
        return (
            f"{self.chromosome_name}: {self.location.lower}-{self.location.upper} ({self.cell_line or 'No Cell Line'})"
        )

    @classmethod
    def search(cls, location: ChromosomeLocation, facets: list[int], region_type: Optional[list[str]] = None):
        from cegs_portal.search.models.reg_effects import (
            RegulatoryEffect,  # Avoid a circular import
        )

        q = Q(chromosome_name=location.chromo, location__overlap=location.range)
        q &= Q(regulatory_effects__count__gt=0)

        if len(facets) > 0:
            q &= Q(facet_values__in=facets)

        if region_type is not None:
            q &= Q(region_type__in=region_type)

        sig_effects = RegulatoryEffect.objects.exclude(direction__exact="non_sig").prefetch_related(
            "targets",
            "targets__parent",
            "target_assemblies",
            "target_assemblies__feature",
            "target_assemblies__feature__parent",
        )

        return (
            cls.objects.annotate(models.Count("regulatory_effects"))
            .prefetch_related(Prefetch("regulatory_effects", queryset=sig_effects), "facet_values")
            .filter(q)
            .select_related(
                "closest_gene",
                "closest_gene__parent",
                "closest_gene_assembly",
                "closest_gene_assembly__feature",
                "closest_gene_assembly__feature__parent",
            )
        )
