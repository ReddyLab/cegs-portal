from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.indexes import GistIndex
from django.db import models

from cegs_portal.search.models.searchable import Searchable
from cegs_portal.search.models.validators import validate_gene_ids


class FeatureAssembly(Searchable):
    class Meta(Searchable.Meta):
        indexes = [
            models.Index(fields=["searchable"], name="%(class)s_srchbl_idx"),
            models.Index(fields=["name"], name="sfa_name_index"),
            models.Index(fields=["chrom_name"], name="sfa_chrom_name_index"),
            models.Index(fields=["feature_type"], name="sfa_feature_type_index"),
            GistIndex(fields=["location"], name="sfa_loc_index"),
            models.Index(fields=["ensembl_id"], name="sfa_ensembl_id_index"),
        ]

    chrom_name = models.CharField(max_length=10)
    ensembl_id = models.CharField(max_length=50, default="No ID")
    ids = models.JSONField(null=True, validators=[validate_gene_ids])

    # These values will be returned as 0-index, half-closed. This should be converted to
    # 1-index, closed for display purposes. 1,c is the default for genomic coordinates
    location = IntegerRangeField()
    name = models.CharField(max_length=50)
    strand = models.CharField(max_length=1, null=True)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)

    # gene, tanscript, etc.
    feature_type = models.CharField(max_length=50)

    # gene_type or transcript_type from gencodeannotation.attributes
    feature_subtype = models.CharField(max_length=50, null=True)

    misc = models.JSONField(null=True)  # exon number, for instance

    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, related_name="children")

    def __str__(self):
        return f"{self.name} -- {self.chrom_name}:{self.location.lower}-{self.location.upper} ({self.ref_genome})"
