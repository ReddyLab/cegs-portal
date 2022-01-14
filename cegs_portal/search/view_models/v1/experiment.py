from django.db.models import F

from cegs_portal.search.models import Experiment


class ExperimentSearch:
    @classmethod
    def id_search(cls, experiment_id):
        experiment = (
            Experiment.objects.filter(id=experiment_id)
            .prefetch_related("data_files", "data_files__cell_lines", "data_files__tissue_types", "other_files")
            .first()
        )
        return experiment

    @classmethod
    def all(cls):
        experiments = (
            Experiment.objects.annotate(
                cell_lines=F("data_files__cell_lines__line_name"),
                tissue_types=F("data_files__tissue_types__tissue_type"),
            )
            .prefetch_related("data_files", "data_files__cell_lines", "data_files__tissue_types", "other_files")
            .all()
        )
        return experiments
