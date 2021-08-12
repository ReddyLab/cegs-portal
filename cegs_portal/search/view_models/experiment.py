from cegs_portal.search.models import Experiment


class ExperimentSearch:
    @classmethod
    def id_search(self, id):
        experiment = Experiment.objects.get(id=id)
        return experiment
