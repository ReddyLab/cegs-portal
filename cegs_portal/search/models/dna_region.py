from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models

from cegs_portal.search.models.facets import FacetedModel
from cegs_portal.search.models.features import Feature, FeatureAssembly
from cegs_portal.search.models.file import File
from cegs_portal.search.models.searchable import Searchable


class DNARegion(Searchable, FacetedModel):
    class Meta(Searchable.Meta):
        indexes = [
            models.Index(fields=["searchable"], name="%(class)s_srchbl_idx"),
            GistIndex(fields=["location"], name="search_region_location_index"),
        ]

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
