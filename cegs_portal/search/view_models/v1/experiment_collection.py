from typing import cast

from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Q, Value

from cegs_portal.search.models import Experiment, ExperimentCollection
from cegs_portal.search.view_models.errors import ObjectNotFoundError


class ExperimentCollectionSearch:
    @classmethod
    def is_public(cls, exprcol_id: str) -> bool:
        collection = ExperimentCollection.objects.filter(accession_id=exprcol_id).values_list("public", flat=True)

        if len(collection) == 0:
            raise ObjectNotFoundError(f"Experiment Collection {exprcol_id} not found")

        return cast(bool, collection[0])

    @classmethod
    def is_archived(cls, exprcol_id: str) -> bool:
        collection = ExperimentCollection.objects.filter(accession_id=exprcol_id).values_list("archived", flat=True)

        if len(collection) == 0:
            raise ObjectNotFoundError(f"Experiment Collection {exprcol_id} not found")

        return cast(bool, collection[0])

    @classmethod
    def id_search(cls, accession_id: str):
        collection = ExperimentCollection.objects.filter(accession_id=accession_id)

        experiments = (
            Experiment.objects.annotate(
                cell_lines=StringAgg("biosamples__cell_line_name", ", ", default=Value("")),
            )
            .filter(collections__accession_id=accession_id)
            .order_by("accession_id")
            .prefetch_related("biosamples")
        )

        return collection, experiments

    @classmethod
    def id_search_public(cls, accession_id: str):
        collection, experiments = cls.id_search(accession_id)
        return collection.filter(public=True, archived=False), experiments.filter(public=True, archived=False)

    @classmethod
    def id_search_with_private(cls, accession_id: str, private_experiment_collections: str, private_experiments: str):
        collection, experiments = cls.id_search(accession_id)
        return collection.filter(
            Q(archived=False) & (Q(public=True) | Q(accession_id__in=private_experiment_collections))
        ), experiments.filter(Q(archived=False) & (Q(public=True) | Q(accession_id__in=private_experiments)))
