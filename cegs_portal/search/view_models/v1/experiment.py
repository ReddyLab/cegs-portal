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
