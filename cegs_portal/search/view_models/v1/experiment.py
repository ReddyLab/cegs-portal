from typing import Optional, cast

from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Q, Value

from cegs_portal.get_expr_data.view_models import (
    experiment_collections_for_facets,
    experiments_for_facets,
    for_facet_query_input,
    public_experiment_collections_for_facets,
    public_experiments_for_facets,
)
from cegs_portal.search.models import Experiment, ExperimentCollection, FacetValue
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
            .select_related("default_analysis", "attribution")
            .prefetch_related("data_files", "biosamples__cell_line", "biosamples__cell_line__tissue_type", "files")
        )
        return experiment

    @classmethod
    def _experiments(cls, facet_ids, experiments, public_query, query, user_type, private_experiments):
        # Filter experiment list by facets, if necessary
        facet_values = for_facet_query_input(facet_ids)
        match facet_values, user_type:
            case [[], [], []], _:
                pass
            case _, UserType.ANONYMOUS:
                facet_experiments = public_query(facet_values)
                experiments = experiments.filter(accession_id__in=facet_experiments)
            case _, UserType.LOGGED_IN:
                facet_experiments = query(facet_values)
                experiments = experiments.filter(accession_id__in=facet_experiments)
            case _, UserType.ADMIN:
                facet_experiments = query(facet_values)
                experiments = experiments.filter(accession_id__in=facet_experiments)

        # Filter experiment list by access level
        match user_type:
            case UserType.ANONYMOUS:
                experiments = experiments.exclude(Q(archived=True) | Q(public=False))
            case UserType.LOGGED_IN:
                if private_experiments is None:
                    private_experiments = []
                experiments = experiments.filter(
                    Q(archived=False) & (Q(public=True) | Q(accession_id__in=private_experiments))
                )
            case UserType.ADMIN:
                # Admins SEE ALL
                pass

        return experiments

    @classmethod
    def experiments(
        cls, facet_ids, user_type: UserType = UserType.ADMIN, private_experiments: Optional[list[str]] = None
    ):
        experiments = (
            Experiment.objects.annotate(
                cell_lines=StringAgg("biosamples__cell_line_name", ", ", default=Value("")),
            )
            .order_by("accession_id")
            .select_related("default_analysis")
            .prefetch_related("biosamples")
        )

        return cls._experiments(
            facet_ids,
            experiments,
            public_experiments_for_facets,
            experiments_for_facets,
            user_type,
            private_experiments,
        )

    @classmethod
    def collections(
        cls, facet_ids, user_type: UserType = UserType.ADMIN, private_experiments: Optional[list[str]] = None
    ):
        return cls._experiments(
            facet_ids,
            ExperimentCollection.objects.order_by("accession_id"),
            public_experiment_collections_for_facets,
            experiment_collections_for_facets,
            user_type,
            private_experiments,
        )

    @classmethod
    def all_except(cls, accession_id):
        return Experiment.objects.exclude(accession_id=accession_id).order_by("accession_id")

    @classmethod
    def _experiment_facet_values(cls, model_class):
        value_ids = model_class.objects.values_list("facet_values__id").distinct("facet_values__id").all()
        value_ids = [fv_id[0] for fv_id in value_ids if fv_id is not None]
        return FacetValue.objects.filter(id__in=value_ids).select_related("facet")

    @classmethod
    def experiment_facet_values(cls):
        return cls._experiment_facet_values(Experiment)

    @classmethod
    def experiment_collection_facet_values(cls):
        return cls._experiment_facet_values(ExperimentCollection)

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
