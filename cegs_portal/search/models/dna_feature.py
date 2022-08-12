from enum import Enum

from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models

from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.facets import Faceted, FacetValue
from cegs_portal.search.models.file import File
from cegs_portal.search.models.searchable import Searchable
from cegs_portal.search.models.validators import validate_gene_ids


class DNAFeatureType(Enum):
    GENE = "gene"
    TRANSCRIPT = "transcript"
    EXON = "exon"
    CCRE = "ccre"
    DHS = "dhs"
    GRNA = "gRNA"


class DNAFeature(Accessioned, Searchable, Faceted):
    class Meta(Accessioned.Meta, Searchable.Meta):
        indexes = [
            models.Index(fields=["name"], name="sdf_name_index"),
            models.Index(fields=["chrom_name"], name="sdf_chrom_name_index"),
            models.Index(fields=["feature_type"], name="sdf_feature_type_index"),
            GistIndex(fields=["location"], name="sdf_loc_index"),
            models.Index(fields=["ensembl_id"], name="sdf_ensembl_id_index"),
        ]

    class Facet(Enum):
        ASSAYS = "Experiment Assays"
        CCRE_CATEGORIES = "cCRE Category"
        DHS_CCRE_OVERLAP_CATEGORIES = "cCRE Overlap"
        GRNA_TYPE = "gRNA Type"

    FEATURE_TYPE = (
        (str(DNAFeatureType.GENE), DNAFeatureType.GENE.value),
        (str(DNAFeatureType.TRANSCRIPT), DNAFeatureType.TRANSCRIPT.value),
        (str(DNAFeatureType.EXON), DNAFeatureType.EXON.value),
        (str(DNAFeatureType.CCRE), DNAFeatureType.CCRE.value),
        (str(DNAFeatureType.DHS), DNAFeatureType.DHS.value),
        (str(DNAFeatureType.GRNA), DNAFeatureType.GRNA.value),
    )

    cell_line = models.CharField(max_length=50, null=True)
    chrom_name = models.CharField(max_length=10)
    ensembl_id = models.CharField(max_length=50, null=True)
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    closest_gene = models.ForeignKey("self", null=True, on_delete=models.SET_NULL, related_name="closest_features")
    closest_gene_distance = models.IntegerField(null=True)
    closest_gene_name = models.CharField(max_length=50, null=True)

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    name = models.CharField(max_length=50)
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)

    feature_type = models.CharField(max_length=50, choices=FEATURE_TYPE, default=DNAFeatureType.GENE)

    # gene_type or transcript_type from gencodeannotation.attributes
    feature_subtype = models.CharField(max_length=50, null=True)

    source = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)

    misc = models.JSONField(null=True)  # exon number, for instance

    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, related_name="children")

    @property
    def assay(self):
        return self.facet_values.get(facet__name=DNAFeature.Facet.ASSAYS.value).value

    @property
    def ccre_category_ids(self):
        return [v.id for v in self.facet_values.filter(facet__name=DNAFeature.Facet.CCRE_CATEGORIES.value).all()]

    @property
    def ccre_overlap_id(self):
        try:
            return self.facet_values.get(facet__name=DNAFeature.Facet.DHS_CCRE_OVERLAP_CATEGORIES.value).id
        except FacetValue.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.name} -- {self.chrom_name}:{self.location.lower}-{self.location.upper} ({self.ref_genome})"
