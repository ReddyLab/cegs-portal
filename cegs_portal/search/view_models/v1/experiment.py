from typing import cast

from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Q, Value

from cegs_portal.search.models import Experiment, FacetValue
from cegs_portal.search.view_models.errors import ObjectNotFoundError


class ExperimentSearch:
    @classmethod
    def is_public(cls, expr_id: str) -> bool:
        experiment = Experiment.objects.filter(accession_id=expr_id).values_list("public", flat=True)

        if len(experiment) == 0:
            raise ObjectNotFoundError(f"Experiment {expr_id} not found")

        return cast(bool, experiment[0])

    @classmethod
    def is_archived(cls, expr_id: str) -> bool:
        experiment = Experiment.objects.filter(accession_id=expr_id).values_list("archived", flat=True)

        if len(experiment) == 0:
            raise ObjectNotFoundError(f"Experiment {expr_id} not found")

        return cast(bool, experiment[0])

    @classmethod
    def accession_search(cls, accession_id):
        experiment = (
            Experiment.objects.filter(accession_id=accession_id)
            .prefetch_related("data_files", "biosamples__cell_line", "biosamples__cell_line__tissue_type", "files")
            .first()
        )
        return experiment

    @classmethod
    def all(cls, facet_ids):
        experiments = Experiment.objects.annotate(
            cell_lines=StringAgg("biosamples__cell_line_name", ", ", default=Value("")),
        ).order_by("accession_id")

        if len(facet_ids) > 0:
            experiments = experiments.filter(facet_values__id__in=facet_ids)

        return experiments

    @classmethod
    def all_public(cls, facet_ids):
        return cls.all(facet_ids).filter(public=True, archived=False)

    @classmethod
    def all_with_private(cls, facet_ids, private_experiments):
        return cls.all(facet_ids).filter(Q(archived=False) & (Q(public=True) | Q(accession_id__in=private_experiments)))

    @classmethod
    def all_except(cls, accession_id):
        return Experiment.objects.exclude(accession_id=accession_id).order_by("accession_id")

    @classmethod
    def experiment_facet_values(cls):
        experiment_facet_value_ids = (
            Experiment.objects.values_list("facet_values__id").distinct("facet_values__id").all()
        )
        experiment_facet_value_ids = [fv_id[0] for fv_id in experiment_facet_value_ids if fv_id is not None]
        return FacetValue.objects.filter(id__in=experiment_facet_value_ids).select_related("facet")
