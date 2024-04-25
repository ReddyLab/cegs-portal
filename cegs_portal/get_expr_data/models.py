import os.path

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, IntegerRangeField
from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.core.files.storage import default_storage
from django.db import connection, models
from django.db.models.expressions import RawSQL

from cegs_portal.search.models.validators import validate_accession_id

EXPR_DATA_DIR = "expr_data_dir"


def expr_data_base_path():
    return os.path.join(default_storage.location, EXPR_DATA_DIR)


class ExperimentData(models.Model):
    class DataState(models.TextChoices):
        IN_PREPARATION = "IN_PREP", "In Preparation"
        READY = "READY", "Ready"
        DELETED = "DELETED", "Deleted"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.CharField(max_length=8, choices=DataState.choices, default=DataState.IN_PREPARATION)
    filename = models.CharField(max_length=256)
    file = models.FilePathField(path=expr_data_base_path, max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)


class ReoSourcesTargets(models.Model):
    class Meta:
        db_table = "get_expr_data_reo_sources_targets"
        indexes = [
            models.Index(fields=["reo_accession"], name="idx_rstm_reo_accession"),
            models.Index(fields=["reo_analysis"], name="idx_rstm_reo_analysis"),
            GistIndex(fields=["source_loc"], name="idx_rstm_source_loc"),
            GistIndex(fields=["target_loc"], name="idx_rstm_target_loc"),
            GinIndex(fields=["cat_facets"], name="idx_rstm_cat_facet"),
            models.Index(
                RawSQL("((reo_facets->>'Raw p value')::numeric)", []),
                name="idx_rstm_pval_asc",
            ),
        ]

    reo_id = models.BigIntegerField()
    archived = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
    reo_accession = models.CharField(max_length=17, validators=[validate_accession_id])
    reo_experiment = models.CharField(max_length=17, validators=[validate_accession_id])
    reo_analysis = models.CharField(max_length=17, validators=[validate_accession_id])
    reo_facets = models.JSONField(null=True, blank=True)
    source_id = models.BigIntegerField()
    source_accession = models.CharField(max_length=17, validators=[validate_accession_id])
    source_chrom = models.CharField(max_length=10)
    source_loc = IntegerRangeField()
    target_id = models.BigIntegerField(null=True, blank=True)
    target_accession = models.CharField(max_length=17, validators=[validate_accession_id], null=True, blank=True)
    target_chrom = models.CharField(max_length=10, null=True, blank=True)
    target_loc = IntegerRangeField(null=True, blank=True)
    target_gene_symbol = models.CharField(max_length=50, null=True, blank=True)
    target_ensembl_id = models.CharField(max_length=50, null=True, blank=True)
    ref_genome = models.CharField(max_length=20)
    cat_facets = ArrayField(models.BigIntegerField())

    @classmethod
    def load_analysis(cls, analysis_accession):
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO get_expr_data_reo_sources_targets
                    (reo_id, archived, public, reo_accession, reo_experiment, reo_analysis, reo_facets,
                    source_id, source_accession, source_chrom, source_loc,
                    target_id, target_accession, target_chrom, target_loc,
                    target_gene_symbol, target_ensembl_id, ref_genome, cat_facets) SELECT
                    sr.id AS reo_id,
                    sr.archived as archived,
                    sr.public as public,
                    sr.accession_id AS reo_accession,
                    sr.experiment_accession_id AS reo_experiment,
                    sr.analysis_accession_id AS reo_analysis,
                    sr.facet_num_values AS reo_facets,
                    sds.id AS source_id,
                    sds.accession_id AS source_accession,
                    sds.chrom_name AS source_chrom,
                    sds.location AS source_loc,
                    sdt.id AS target_id,
                    sdt.accession_id AS target_accession,
                    sdt.chrom_name AS target_chrom,
                    sdt.location AS target_loc,
                    sdt.name AS target_gene_symbol,
                    sdt.ensembl_id AS target_ensembl_id,
                    sedfi.ref_genome AS ref_genome,
                    array_remove(ARRAY_AGG(DISTINCT(srfv.facetvalue_id)) || ARRAY_AGG(DISTINCT(sdsfv.facetvalue_id)) || ARRAY_AGG(DISTINCT(sdtfv.facetvalue_id)), NULL) AS cat_facets
                FROM search_regulatoryeffectobservation AS sr
                LEFT JOIN search_regulatoryeffectobservation_facet_values as srfv on sr.id = srfv.regulatoryeffectobservation_id
                LEFT JOIN search_regulatoryeffectobservation_sources AS srs ON sr.id = srs.regulatoryeffectobservation_id
                LEFT JOIN search_regulatoryeffectobservation_targets AS srt ON sr.id = srt.regulatoryeffectobservation_id
                LEFT JOIN search_dnafeature AS sds ON sds.id = srs.dnafeature_id
                LEFT JOIN search_dnafeature_facet_values as sdsfv on sds.id = sdsfv.dnafeature_id
                LEFT JOIN search_dnafeature AS sdt ON sdt.id = srt.dnafeature_id
                LEFT JOIN search_dnafeature_facet_values as sdtfv on sdt.id = sdtfv.dnafeature_id
                LEFT JOIN search_analysis AS sa ON sr.analysis_accession_id = sa.accession_id
                LEFT JOIN search_file AS sf ON sa.id = sf.analysis_id
                LEFT JOIN search_experimentdatafileinfo AS sedfi ON sf.data_file_info_id = sedfi.id
                WHERE sr.analysis_accession_id = %s
                GROUP BY sr.id, sds.id, sdt.id, sedfi.ref_genome""",
                [analysis_accession],
            )

    def __str__(self):
        return f"{self.reo_analysis}: {self.source_accession} -> {self.target_accession}: {self.reo_facets}"


class ReoSourcesTargetsSigOnly(models.Model):
    class Meta:
        db_table = "get_expr_data_reo_sources_targets_sig_only"
        indexes = [
            models.Index(fields=["reo_accession"], name="idx_rstsom_reo_accession"),
            models.Index(fields=["reo_analysis"], name="idx_rstsom_reo_analysis"),
            GistIndex(fields=["source_loc"], name="idx_rstsom_source_loc"),
            GistIndex(fields=["target_loc"], name="idx_rstsom_target_loc"),
            GinIndex(fields=["cat_facets"], name="idx_rstsom_cat_facet"),
            models.Index(
                RawSQL("((reo_facets->>'Raw p value')::numeric)", []),
                name="idx_rstsom_pval_asc",
            ),
        ]

    reo_id = models.BigIntegerField()
    archived = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
    reo_accession = models.CharField(max_length=17, validators=[validate_accession_id])
    reo_experiment = models.CharField(max_length=17, validators=[validate_accession_id])
    reo_analysis = models.CharField(max_length=17, validators=[validate_accession_id])
    reo_facets = models.JSONField(null=True, blank=True)
    source_id = models.BigIntegerField()
    source_accession = models.CharField(max_length=17, validators=[validate_accession_id])
    source_chrom = models.CharField(max_length=10)
    source_loc = IntegerRangeField()
    target_id = models.BigIntegerField(null=True, blank=True)
    target_accession = models.CharField(max_length=17, validators=[validate_accession_id], null=True, blank=True)
    target_chrom = models.CharField(max_length=10, null=True, blank=True)
    target_loc = IntegerRangeField(null=True, blank=True)
    target_gene_symbol = models.CharField(max_length=50, null=True, blank=True)
    target_ensembl_id = models.CharField(max_length=50, null=True, blank=True)
    ref_genome = models.CharField(max_length=20)
    cat_facets = ArrayField(models.BigIntegerField())

    @classmethod
    def load_analysis(cls, analysis_accession):
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO get_expr_data_reo_sources_targets_sig_only
                    (reo_id, archived, public, reo_accession, reo_experiment, reo_analysis, reo_facets,
                    source_id, source_accession, source_chrom, source_loc,
                    target_id, target_accession, target_chrom, target_loc,
                    target_gene_symbol, target_ensembl_id, ref_genome, cat_facets) SELECT
                    sr.id AS reo_id,
                    sr.archived as archived,
                    sr.public as public,
                    sr.accession_id AS reo_accession,
                    sr.experiment_accession_id AS reo_experiment,
                    sr.analysis_accession_id AS reo_analysis,
                    sr.facet_num_values AS reo_facets,
                    sds.id AS source_id,
                    sds.accession_id AS source_accession,
                    sds.chrom_name AS source_chrom,
                    sds.location AS source_loc,
                    sdt.id AS target_id,
                    sdt.accession_id AS target_accession,
                    sdt.chrom_name AS target_chrom,
                    sdt.location AS target_loc,
                    sdt.name AS target_gene_symbol,
                    sdt.ensembl_id AS target_ensembl_id,
                    sedfi.ref_genome AS ref_genome,
                    array_remove(ARRAY_AGG(DISTINCT(srfv.facetvalue_id)) || ARRAY_AGG(DISTINCT(sdsfv.facetvalue_id)) || ARRAY_AGG(DISTINCT(sdtfv.facetvalue_id)), NULL) AS cat_facets
                FROM search_regulatoryeffectobservation AS sr
                LEFT JOIN search_regulatoryeffectobservation_facet_values as srfv on sr.id = srfv.regulatoryeffectobservation_id
                LEFT JOIN search_regulatoryeffectobservation_sources AS srs ON sr.id = srs.regulatoryeffectobservation_id
                LEFT JOIN search_regulatoryeffectobservation_targets AS srt ON sr.id = srt.regulatoryeffectobservation_id
                LEFT JOIN search_dnafeature AS sds ON sds.id = srs.dnafeature_id
                LEFT JOIN search_dnafeature_facet_values as sdsfv on sds.id = sdsfv.dnafeature_id
                LEFT JOIN search_dnafeature AS sdt ON sdt.id = srt.dnafeature_id
                LEFT JOIN search_dnafeature_facet_values as sdtfv on sdt.id = sdtfv.dnafeature_id
                LEFT JOIN search_analysis AS sa ON sr.analysis_accession_id = sa.accession_id
                LEFT JOIN search_file AS sf ON sa.id = sf.analysis_id
                LEFT JOIN search_experimentdatafileinfo AS sedfi ON sf.data_file_info_id = sedfi.id
                WHERE sr.analysis_accession_id = %s AND srfv.facetvalue_id != (SELECT id FROM search_facetvalue where value = 'Non-significant')
                GROUP BY sr.id, sds.id, sdt.id, sedfi.ref_genome""",
                [analysis_accession],
            )

    def __str__(self):
        return f"{self.reo_analysis}: {self.source_accession} -> {self.target_accession}: {self.reo_facets}"
