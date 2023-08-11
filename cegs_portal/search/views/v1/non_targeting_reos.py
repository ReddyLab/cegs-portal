from django.core.paginator import Paginator
from django.http import Http404

from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, DNAFeatureNonTargetSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    TemplateJsonView,
)
from cegs_portal.utils.pagination_types import Pageable


class NonTargetRegEffectsView(ExperimentAccessMixin, TemplateJsonView):
    json_renderer = ""
    template = "search/v1/non_targeting_reos.html"
    template_data_name = "non_targeting_reos"
    page_title = ""

    def get_experiment_accession_id(self):
        try:
            return DNAFeatureNonTargetSearch.expr_id(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_public(self):
        try:
            return DNAFeatureNonTargetSearch.is_public(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_archived(self):
        try:
            return DNAFeatureNonTargetSearch.is_archived(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            format
                * genoverse
            page
                * an integer > 0
            sig_only
                * whether or not to include only significant observations
        """

        def get_sig_only(value):
            if value == "0" or value == "false" or value == "False":
                return False
            else:
                return True

        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        sig_only = request.GET.get("sig _only", True)
        options["sig_only"] = get_sig_only(sig_only)

        return options


    def get_data(self, options, feature_id) -> Pageable[RegulatoryEffectObservation]:
        non_targeting_reos = []
        reg_effects = DNAFeatureNonTargetSearch.non_targeting_regeffect_search(feature_id, options.get("sig_only"))

        if reg_effects.exists():
            non_targeting_reos.extend(list(reg_effects))

        return non_targeting_reos

