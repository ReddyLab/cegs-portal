from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from cegs_portal.search.views.view_utils import TSV_MIME

from cegs_portal.search.json_templates.v1.non_targeting_reos import (
    non_targeting_regulatory_effects,
)
from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureNonTargetSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    TemplateJsonView,
)
from cegs_portal.utils.pagination_types import Pageable


def non_targeting_regulatory_effects_tsv(data):
    reo_page, feature = data
    tsv_data = []
    tsv_data.append(['Chromosome Location', 'Effect Size', 'Direction', 'Significance', 'Distance', 'Feature Type', 'Experiment'])

    for reo in reo_page:
        first_source = reo.sources.all()[0]
        row = [first_source.chrom_name, first_source.location.lower, first_source.location.upper, reo.effect_size, reo.direction, reo.significance, first_source.closest_gene_distance, first_source.get_feature_type_display(), reo.experiment.name]

        tsv_data.append(row)

    return tsv_data


class NonTargetRegEffectsView(ExperimentAccessMixin, TemplateJsonView):
    json_renderer = non_targeting_regulatory_effects
    tsv_renderer = non_targeting_regulatory_effects_tsv
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

        return options

    def get(self, request, options, data, feature_id):
        if request.headers.get('Accept') == TSV_MIME:
            tsv_data = self.tsv_renderer(data)
            return TsvResponse(tsv_data)
        else:
            reo_page, feature = data
            response_values = {"non_targeting_reos": reo_page, "feature": feature}

            if request.headers.get("HX-Target"):
                return render(
                    request,
                    "search/v1/partials/_non_targeting_reo.html",
                    response_values,
                )

            return super().get(request, options, response_values)

    def get_data(self, options, feature_id) -> Pageable[RegulatoryEffectObservation]:
        non_targeting_reos = []
        feature = DNAFeatureNonTargetSearch.id_feature_search(feature_id)
        reg_effects = DNAFeatureNonTargetSearch.non_targeting_regeffect_search(feature_id, options.get("sig_only"))

        if reg_effects.exists():
            non_targeting_reos.extend(list(reg_effects))

        return Paginator(non_targeting_reos, options["per_page"]).get_page(options["page"]), feature
