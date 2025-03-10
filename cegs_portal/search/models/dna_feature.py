from enum import Enum
from typing import Optional

from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.db.models.functions import Upper

from cegs_portal.search.models.access_control import AccessControlled
from cegs_portal.search.models.accession import Accessioned
from cegs_portal.search.models.dna_feature_type import DNAFeatureType
from cegs_portal.search.models.experiment import Analysis, Experiment
from cegs_portal.search.models.facets import Faceted, FacetValue
from cegs_portal.search.models.file import File
from cegs_portal.search.models.validators import validate_gene_ids


class GrnaType(Enum):
    POSITIVE_CONTROL = "Positive Control"
    NEGATIVE_CONTROL = "Negative Control"
    TARGETING = "Targeting"


class PromoterType(Enum):
    PROMOTER = "Promoter"
    NON_PROMOTER = "Non-promoter"


class CCRECategoryType(Enum):
    PLS = "PLS"
    PELS = "pELS"
    DELS = "dELS"
    DNASE = "DNase-H3K4me3"
    CTCF_ONLY = "CTCF-only"
    CTCF_BOUND = "CTCF-bound"


class DNAFeature(Accessioned, Faceted, AccessControlled):
    class Meta(Accessioned.Meta):
        indexes = [
            models.Index(fields=["name"], name="sdf_name_index"),
            models.Index(Upper("name"), name="sdf_name_insensitive_index"),
            models.Index(fields=["chrom_name"], name="sdf_chrom_name_index"),
            models.Index(fields=["feature_type"], name="sdf_feature_type_index"),
            GistIndex(fields=["location"], name="sdf_loc_index"),
            models.Index(fields=["ensembl_id"], name="sdf_ensembl_id_index"),
            models.Index(fields=["accession_id"], name="sdf_accession_id_index"),
        ]

    class Facet(Enum):
        ASSAYS = "Experiment Assays"
        CCRE_CATEGORIES = "cCRE Category"
        DHS_CCRE_OVERLAP_CATEGORIES = "cCRE Overlap"
        GRNA_TYPE = "gRNA Type"
        PROMOTER = "Promoter Classification"

    FEATURE_TYPE = (
        (str(DNAFeatureType.GENE), DNAFeatureType.GENE.value),
        (str(DNAFeatureType.TRANSCRIPT), DNAFeatureType.TRANSCRIPT.value),
        (str(DNAFeatureType.EXON), DNAFeatureType.EXON.value),
        (str(DNAFeatureType.CCRE), DNAFeatureType.CCRE.value),
        (str(DNAFeatureType.DHS), DNAFeatureType.DHS.value),
        (str(DNAFeatureType.GRNA), DNAFeatureType.GRNA.value),
        (str(DNAFeatureType.CAR), DNAFeatureType.CAR.value),
        (str(DNAFeatureType.CRE), DNAFeatureType.CRE.value),
        (str(DNAFeatureType.GE), DNAFeatureType.GE.value),
    )

    cell_line = models.CharField(max_length=50, null=True, blank=True)
    chrom_name = models.CharField(max_length=10)
    ensembl_id = models.CharField(max_length=50, null=True, blank=True)
    ids = models.JSONField(null=True, validators=[validate_gene_ids], blank=True)

    closest_gene = models.ForeignKey(
        "self", null=True, on_delete=models.SET_NULL, related_name="closest_features", blank=True
    )
    closest_gene_distance = models.IntegerField(null=True, blank=True)
    closest_gene_name = models.CharField(max_length=50, null=True, blank=True)
    closest_gene_ensembl_id = models.CharField(max_length=50, null=True, blank=True)

    associated_ccres = models.ManyToManyField("self", blank=True)

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    name = models.CharField(max_length=50, null=True, blank=True)
    strand = models.CharField(max_length=1, null=True, blank=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10, default="0")

    feature_type = models.CharField(max_length=50, choices=FEATURE_TYPE, default=DNAFeatureType.GENE)

    # gene_type or transcript_type from gencodeannotation.attributes
    feature_subtype = models.CharField(max_length=50, null=True, blank=True)

    source_file = models.ForeignKey(File, null=True, on_delete=models.SET_NULL, blank=True)

    misc = models.JSONField(null=True, blank=True)  # exon number, for instance

    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, related_name="children", blank=True)
    parent_accession = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        to_field="accession_id",
        db_column="parent_accession_id",
        related_name="children_accession",
        blank=True,
    )

    experiment_accession = models.ForeignKey(
        Experiment,
        null=True,
        to_field="accession_id",
        db_column="experiment_accession_id",
        related_name="+",
        on_delete=models.CASCADE,
        blank=True,
    )
    experiment_accession_id: Optional[str]

    analysis = models.ForeignKey(
        Analysis,
        null=True,
        to_field="accession_id",
        db_column="analysis_accession_id",
        related_name="+",
        on_delete=models.CASCADE,
        blank=True,
    )
    analysis_accession_id: Optional[str]

    # Are any REOs this feature is a source for significant
    significant_reo = models.BooleanField(default=False)

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
        return f"{self.chrom_name}:{self.location.lower}-{self.location.upper} ({self.ref_genome})"
