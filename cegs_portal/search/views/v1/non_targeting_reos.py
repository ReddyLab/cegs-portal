from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render

from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.json_templates.v1.non_targeting_reos import (
    non_targeting_regulatory_effects,
)
from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.search.tsv_templates.v1.non_targeting_reos import (
    non_targeting_regulatory_effects as ntre_data,
)
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureNonTargetSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    MultiResponseFormatView,
)
from cegs_portal.utils import truthy_to_bool
from cegs_portal.utils.pagination_types import Pageable


class NonTargetRegEffectsView(ExperimentAccessMixin, MultiResponseFormatView):
    json_renderer = non_targeting_regulatory_effects
    tsv_renderer = ntre_data
    template = "search/v1/non_targeting_reos.html"
    page_title = ""

    def get_experiment_accession_id(self):
        try:
            return DNAFeatureNonTargetSearch.expr_id(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(f"DNA Feature {self.kwargs['feature_id']} not found") from e

    def is_public(self):
        try:
            return DNAFeatureNonTargetSearch.is_public(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(f"DNA Feature {self.kwargs['feature_id']} not found") from e

    def is_archived(self):
        try:
            return DNAFeatureNonTargetSearch.is_archived(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(f"DNA Feature {self.kwargs['feature_id']} not found") from e

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
            per_page
                * an integer > 0
            sig_only
                * whether or not to include only significant observations
        """

        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        options["sig_only"] = truthy_to_bool(request.GET.get("sig_only", True))
        options["tsv_format"] = request.GET.get("tsv_format", None)

        return options

    def get(self, request, options, data, feature_id):
        reo_page, feature = data
        response_values = {"non_targeting_reos": reo_page, "feature": feature}

        if request.headers.get("HX-Target"):
            return render(
                request,
                "search/v1/partials/_non_targeting_reo.html",
                response_values,
            )

        return super().get(request, options, response_values)

    def get_tsv(self, request, options, data, feature_id):
        _, feature = data
        if is_bed6(options):
            filename = f"{feature.name}_proximal_regulatory_observations_table_data.bed"
        else:
            filename = f"{feature.name}_proximal_regulatory_observations_table_data.tsv"
        return super().get_tsv(request, options, data, filename=filename)

    def get_data(self, options, feature_id) -> Pageable[RegulatoryEffectObservation]:
        non_targeting_reos = []
        feature = DNAFeatureNonTargetSearch.id_feature_search(feature_id)
        reg_effects = DNAFeatureNonTargetSearch.non_targeting_regeffect_search(feature_id, options.get("sig_only"))

        if reg_effects.exists():
            non_targeting_reos.extend(list(reg_effects))

        return Paginator(non_targeting_reos, options["per_page"]).get_page(options["page"]), feature
