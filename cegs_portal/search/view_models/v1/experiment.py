from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Value

from cegs_portal.search.models import Experiment


class ExperimentSearch:
    @classmethod
    def accession_search(cls, accession_id):
        experiment = (
            Experiment.objects.filter(accession_id=accession_id)
            .prefetch_related("data_files", "data_files__cell_lines", "data_files__tissue_types", "other_files")
            .first()
        )
        return experiment

    @classmethod
    def all(cls):
        experiments = (
            Experiment.objects.annotate(
                cell_lines=StringAgg("data_files__cell_line", ", ", default=Value("")),
            )
            .order_by("accession_id")
            .all()
        )
        return experiments

    @classmethod
    def all_except(cls, accession_id):
        return Experiment.objects.exclude(accession_id=accession_id).order_by("accession_id")
