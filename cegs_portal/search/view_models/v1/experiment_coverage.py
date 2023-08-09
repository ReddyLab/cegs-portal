from cegs_portal.search.models import Experiment


class ExperimentCoverageSearch:
    @classmethod
    def default_analyses(cls, expr_ids: list[str]) -> list[tuple[str, str]]:
        return list(
            Experiment.objects.filter(accession_id__in=expr_ids)
            .select_related("default_analysis")
            .values_list("accession_id", "default_analysis__accession_id")
        )
