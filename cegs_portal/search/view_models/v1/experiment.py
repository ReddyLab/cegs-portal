from typing import cast

from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Q, Value

from cegs_portal.get_expr_data.view_models import (
    experiments_for_facets,
    for_facet_query_input,
    public_experiments_for_facets,
)
from cegs_portal.search.models import Experiment, FacetValue
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.users.models import UserType


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
    def experiment_statuses(cls, expr_ids: list[str]) -> bool:
        experiments = Experiment.objects.filter(accession_id__in=expr_ids).values_list(
            "accession_id", "public", "archived"
        )

        if len(experiments) == 0:
            raise ObjectNotFoundError(f"Experiments {expr_ids} not found")

        return experiments

    @classmethod
    def accession_search(cls, accession_id: str):
        return cls.multi_accession_search([accession_id]).first()

    @classmethod
    def multi_accession_search(cls, accession_ids: list[str]):
        experiment = (
            Experiment.objects.filter(accession_id__in=accession_ids)
            .select_related("default_analysis")
            .prefetch_related("data_files", "biosamples__cell_line", "biosamples__cell_line__tissue_type", "files")
        )
        return experiment

    @classmethod
    def all(cls, facet_ids, user_type: UserType = UserType.ANONYMOUS):
        facet_query_input = for_facet_query_input(facet_ids)

        experiments = (
            Experiment.objects.annotate(
                cell_lines=StringAgg("biosamples__cell_line_name", ", ", default=Value("")),
            )
            .order_by("accession_id")
            .prefetch_related("biosamples")
        )
        match facet_ids, user_type:
            case [], _:
                pass
            case _, UserType.ANONYMOUS:
                facet_experiments = public_experiments_for_facets(facet_query_input)
                experiments = experiments.filter(accession_id__in=facet_experiments)
            case _, UserType.LOGGED_IN:
                facet_experiments = experiments_for_facets(facet_query_input)
                experiments = experiments.filter(accession_id__in=facet_experiments)
            case _, UserType.ADMIN:
                facet_experiments = experiments_for_facets(facet_query_input)
                experiments = experiments.filter(accession_id__in=facet_experiments)

        return experiments

    @classmethod
    def all_public(cls, facet_ids):
        return cls.all(facet_ids, UserType.ANONYMOUS)

    @classmethod
    def all_with_private(cls, facet_ids, private_experiments):
        return cls.all(facet_ids, UserType.LOGGED_IN).filter(
            Q(archived=False) & (Q(public=True) | Q(accession_id__in=private_experiments))
        )

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

    @classmethod
    def default_analysis_id_search(cls, expr_id: str):
        queryset = Experiment.objects.filter(accession_id=expr_id)
        default_analysis_list = queryset.values_list("default_analysis__accession_id", flat=True)
        if default_analysis_list:
            default_analysis = default_analysis_list[0]
        else:
            default_analysis = None
        return default_analysis

    @classmethod
    def all_analysis_id_search(cls, expr_id: str):
        queryset = Experiment.objects.filter(accession_id=expr_id)
        analysis_id = queryset.values_list("analyses__accession_id", flat=True).order_by("analyses__id")
        return analysis_id
