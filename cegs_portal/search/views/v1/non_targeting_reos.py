from django.core.paginator import Paginator
from django.http import Http404

from cegs_portal.search.json_templates.v1.non_targeting_reos import (
    datatables_non_target_regulatory_effect,
)
from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureNonTargetSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    TemplateJsonView,
)
from cegs_portal.utils.pagination_types import Pageable


class NonTargetRegEffectsView(ExperimentAccessMixin, TemplateJsonView):
    json_renderer = datatables_non_target_regulatory_effect
    template = "search/v1/non_targeting_reos.html"
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
        sig_only = request.GET.get("sig_only", True)
        options["sig_only"] = get_sig_only(sig_only)
        options["draw"] = int(request.GET.get("draw", 0))

        return options

    def get(self, request, options, data, feature_id):
        reo_pages, feature = data
        reos = []
        for reo in reo_pages.get_page(options["page"]):
            reos.append(
                {
                    "accession_id": reo.accession_id,
                    "effect_size": reo.effect_size,
                    "direction": reo.direction,
                    "significance": reo.significance,
                    "experiment_name": reo.experiment.name,
                    "experiment_accession_id": reo.experiment.accession_id,
                    "first_source": reo.sources.all()[0],
                }
            )
        return super().get(request, options, {"non_targeting_reos": reos, "feature": feature})

    def get_data(self, options, feature_id) -> Pageable[RegulatoryEffectObservation]:
        non_targeting_reos = []
        feature = DNAFeatureNonTargetSearch.id_feature_search(feature_id)
        reg_effects = DNAFeatureNonTargetSearch.non_targeting_regeffect_search(feature_id, options.get("sig_only"))

        if reg_effects.exists():
            non_targeting_reos.extend(list(reg_effects))

        return Paginator(non_targeting_reos, options["per_page"]), feature
