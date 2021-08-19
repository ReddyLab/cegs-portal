from cegs_portal.search.models import Experiment


class ExperimentSearch:
    @classmethod
    def id_search(cls, experiment_id):
        experiment = Experiment.objects.get(id=experiment_id)
        return experiment
