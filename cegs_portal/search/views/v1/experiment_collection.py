from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404

from cegs_portal.search.json_templates.v1.experiment_collection import (
    experiment_collection,
)
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import ExperimentCollectionSearch
from cegs_portal.search.views.custom_views import MultiResponseFormatView


class ExperimentCollectionView(UserPassesTestMixin, MultiResponseFormatView):
    json_renderer = experiment_collection
    template = "search/v1/experiment_collection.html"

    def test_func(self):
        if self.is_archived() and (self.request.user.is_anonymous or not self.request.user.is_portal_admin):
            self.raise_exception = True  # Don't redirect to login
            return False

        if self.is_public():
            return True

        if self.request.user.is_anonymous:
            return False

        return (
            self.request.user.is_superuser
            or self.request.user.is_portal_admin
            or self.kwargs["expcol_id"] in self.request.user.all_experiment_collections()
        )

    def is_public(self):
        try:
            return ExperimentCollectionSearch.is_public(self.kwargs["expcol_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_archived(self):
        try:
            return ExperimentCollectionSearch.is_archived(self.kwargs["expcol_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def get(self, request, options, data, expcol_id):
        collection, experiments = data
        return super().get(
            request,
            options,
            {"collection": collection, "experiments": experiments},
        )

    def get_data(self, options, expcol_id):
        if self.request.user.is_anonymous:
            collection, experiments = ExperimentCollectionSearch.id_search_public(expcol_id)
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            collection, experiments = ExperimentCollectionSearch.id_search(expcol_id)
        else:
            collection, experiments = ExperimentCollectionSearch.id_search_with_private(
                expcol_id, self.request.user.all_experiment_collections(), self.request.user.all_experiments()
            )

        if len(collection) == 0:
            raise Http404(f"Experiment Collection {expcol_id} was not found")

        return collection.first(), experiments
