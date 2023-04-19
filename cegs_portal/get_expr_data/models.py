from django.conf import settings
from django.db import connection, models


class ExperimentData(models.Model):
    class DataState(models.TextChoices):
        IN_PREPARATION = "IN_PREP", "In Preparation"
        READY = "READY", "Ready"
        DELETED = "DELETED", "Deleted"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.CharField(max_length=8, choices=DataState.choices, default=DataState.IN_PREPARATION)
    data = models.FileField(upload_to="expr_data")


# This is a non-managed table because it's really a "Materialized View" (See
# https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
#
# This model class isn't used, but the materialized view itself is, when getting experiment data
# for a set of regions. See `retrieve_experiment_data` in cegs_portal/get_expr_data/view_models.py.
# The materialized view is a necessary query optimization. Otherwise getting the experiment data is
# Extremely slow.
# You can see the data definition in cegs_portal/get_expr_data/migrations/0005_auto_20230418_1148.py
class ReoSourcesTargets(models.Model):
    class Meta:
        managed = False
        db_table = "reo_sources_targets"

    @classmethod
    def refresh_view(cls):
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW reo_sources_targets")

    @classmethod
    def view_contents(cls):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM reo_sources_targets")
            return cursor.fetchall()
