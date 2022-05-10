from enum import Enum

from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models

from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.facets import Faceted
from cegs_portal.search.models.features import FeatureAssembly
from cegs_portal.search.models.file import File
from cegs_portal.search.models.searchable import Searchable


class DNARegion(Accessioned, Searchable, Faceted):
    class Meta(Searchable.Meta):
        indexes = [
            GistIndex(fields=["location"], name="search_region_location_index"),
        ]

    class Facet(Enum):
        ASSAYS = "Experiment Assays"
        CCRE_CATEGORIES = "cCRE Category"
        DHS_CCRE_OVERLAP_CATEGORIES = "cCRE Overlap"

    cell_line = models.CharField(max_length=50, null=True)
    chrom_name = models.CharField(max_length=10)
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

    @property
    def assay(self):
        return self.facet_values.get(facet__name=DNARegion.Facet.ASSAYS.value).value

    @property
    def ccre_category_ids(self):
        return [v.id for v in self.facet_values.filter(facet__name=DNARegion.Facet.CCRE_CATEGORIES.value).all()]

    @property
    def ccre_overlap_id(self):
        return self.facet_values.get(facet__name=DNARegion.Facet.DHS_CCRE_OVERLAP_CATEGORIES.value).id

    def __str__(self):
        return f"{self.chrom_name}: {self.location.lower}-{self.location.upper} ({self.cell_line or 'No Cell Line'})"
