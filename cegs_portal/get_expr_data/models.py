import os.path

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection, models

EXPR_DATA_DIR = "expr_data_dir"
EXPR_DATA_BASE_PATH = os.path.join(default_storage.location, EXPR_DATA_DIR)


class ExperimentData(models.Model):
    class DataState(models.TextChoices):
        IN_PREPARATION = "IN_PREP", "In Preparation"
        READY = "READY", "Ready"
        DELETED = "DELETED", "Deleted"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.CharField(max_length=8, choices=DataState.choices, default=DataState.IN_PREPARATION)
    filename = models.CharField(max_length=256)
    file = models.FilePathField(path=EXPR_DATA_BASE_PATH, max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)


# This is a non-managed table because it's really a "Materialized View" (See
# https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
#
# This model class isn't used, but the materialized view itself is, when getting experiment data
# for a set of regions. See `retrieve_experiment_data` in cegs_portal/get_expr_data/view_models.py.
# The materialized view is a necessary query optimization. Otherwise getting the experiment data is
# Extremely slow.
# You can see the data definition in cegs_portal/get_expr_data/migrations/0010_auto_20230504_1329.py
class ReoSourcesTargets(models.Model):
    class Meta:
        managed = False
        db_table = "reo_sources_targets"

    @classmethod
    def refresh_view(cls):
        with connection.cursor() as cursor:
            # Drop indices because refreshing the view may take a long time if they already exist
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets.idx_rst_reo_accession")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets.idx_rst_source_loc")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets.idx_rst_target_loc")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets.idx_rst_cat_facet")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets.idx_rst_pval_asc")

            cursor.execute("REFRESH MATERIALIZED VIEW reo_sources_targets")

            # Add indices back
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rst_reo_accession ON reo_sources_targets (reo_accession)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_rst_source_loc ON reo_sources_targets USING GIST (source_loc)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_rst_target_loc ON reo_sources_targets USING GIST (target_loc)"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rst_cat_facet ON reo_sources_targets USING GIN (cat_facets)")
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_rst_pval_asc
                       ON reo_sources_targets (((reo_facets->>'Raw p value')::numeric) ASC)"""
            )

            cursor.execute("ANALYZE reo_sources_targets")

    @classmethod
    def view_contents(cls):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM reo_sources_targets")
            return cursor.fetchall()


# This is a non-managed table because it's really a "Materialized View" (See
# https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
#
# This model class isn't used, but the materialized view itself is, when getting experiment data
# for a set of regions. See `sig_reo_loc_search` in cegs_portal/search/view_models/v1/search.py.
# The materialized view is a necessary query optimization. Otherwise getting the experiment data is
# Extremely slow.
#
# This table is basically the same as ReoSourcesTargets, but it only contains significant observations.
# Without non-significant observations the table is orders of magnitude smaller and thus much faster to
# query.
#
# You can see the data definition in cegs_portal/get_expr_data/migrations/0011_auto_20230516_1123.py
class ReoSourcesTargetsSigOnly(models.Model):
    class Meta:
        managed = False
        db_table = "reo_sources_targets_sig_only"

    @classmethod
    def refresh_view(cls):
        with connection.cursor() as cursor:
            # Drop indices because refreshing the view may take a long time if they already exist
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets_sig_only.idx_rstso_reo_accession")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets_sig_only.idx_rstso_source_loc")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets_sig_only.idx_rstso_target_loc")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets_sig_only.idx_rstso_cat_facet")
            cursor.execute("DROP INDEX IF EXISTS reo_sources_targets_sig_only.idx_rstso_pval_asc")

            cursor.execute("REFRESH MATERIALIZED VIEW reo_sources_targets_sig_only")

            # Add indices back
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_rstso_reo_accession
                       ON reo_sources_targets_sig_only (reo_accession)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_rstso_source_loc
                       ON reo_sources_targets_sig_only USING GIST (source_loc)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_rstso_target_loc
                       ON reo_sources_targets_sig_only USING GIST (target_loc)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_rstso_cat_facet
                       ON reo_sources_targets_sig_only USING GIN (cat_facets)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_rstso_pval_asc
                       ON reo_sources_targets_sig_only (((reo_facets->>'Raw p value')::numeric) ASC)"""
            )

            cursor.execute("ANALYZE reo_sources_targets_sig_only")

    @classmethod
    def view_contents(cls):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM reo_sources_targets_sig_only")
            return cursor.fetchall()
