from django.core.paginator import Paginator
from django.http import Http404

from cegs_portal.search.json_templates.v1.feature_reg_effects import feature_reg_effects
from cegs_portal.search.json_templates.v1.reg_effect import regulatory_effect
from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation
from cegs_portal.search.tsv_templates.v1.reg_effects import reg_effects as re_data
from cegs_portal.search.tsv_templates.v1.reg_effects import (
    target_reg_effects as target_data,
)
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, RegEffectSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    MultiResponseFormatView,
)
from cegs_portal.utils.pagination_types import Pageable


class RegEffectView(ExperimentAccessMixin, MultiResponseFormatView):
    """
    Headers used:
        accept
            * application/json
    """

    json_renderer = regulatory_effect
    template = "search/v1/reg_effect.html"
    template_data_name = "regulatory_effect"

    def get_experiment_accession_id(self):
        try:
            return RegEffectSearch.expr_id(self.kwargs["re_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_public(self):
        try:
            return RegEffectSearch.is_public(self.kwargs["re_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_archived(self):
        try:
            return RegEffectSearch.is_archived(self.kwargs["re_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def get_data(self, _options, re_id):
        search_results = RegEffectSearch.id_search(re_id)

        cell_lines = set()
        tissue_types = set()
        for bios in search_results.experiment.biosamples.all():
            cell_lines.add(bios.cell_line)
            tissue_types.add(bios.cell_line.tissue_type_name)
        setattr(search_results, "cell_lines", cell_lines)
        setattr(search_results, "tissue_types", tissue_types)

        return search_results


class FeatureEffectsView(ExperimentAccessMixin, MultiResponseFormatView):
    json_renderer = feature_reg_effects
    template = ""
    template_data_name = "regeffects"
    page_title = ""

    def get_experiment_accession_id(self):
        try:
            return DNAFeatureSearch.expr_id(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_public(self):
        try:
            return DNAFeatureSearch.is_public(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_archived(self):
        try:
            return DNAFeatureSearch.is_archived(self.kwargs["feature_id"])
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
        options["tsv_format"] = request.GET.get("tsv_format", None)

        return options

    def get(self, request, options, data, *args, **kwargs):
        reg_effect_paginator = Paginator(data, options["per_page"])
        reg_effect_page = reg_effect_paginator.get_page(options["page"])

        return super().get(request, options, reg_effect_page, *args, **kwargs)

    def get_json(self, request, options, data, *args, **kwargs):
        reg_effect_paginator = Paginator(data, options["per_page"])
        reg_effect_page = reg_effect_paginator.get_page(options["page"])

        return super().get_json(request, options, reg_effect_page, *args, **kwargs)

    def get_data(self, options, feature_id) -> Pageable[RegulatoryEffectObservation]:
        raise NotImplementedError("FeatureEffectsView.get_data")


class SourceEffectsView(FeatureEffectsView):
    template = "search/v1/source_reg_effects.html"
    tsv_renderer = re_data

    def get_data(self, options, feature_id) -> Pageable[RegulatoryEffectObservation]:
        if self.request.user.is_anonymous:
            reg_effects = RegEffectSearch.source_search_public(feature_id, options.get("sig_only"))
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            reg_effects = RegEffectSearch.source_search(feature_id, options.get("sig_only"))
        else:
            reg_effects = RegEffectSearch.source_search_with_private(
                feature_id, options.get("sig_only"), self.request.user.all_experiments()
            )

        return reg_effects

    def get_tsv(self, request, options, data, feature_id):
        if options is not None and options.get("tsv_format", None) == "bed6":
            filename = f"{feature_id}_source_for_regulatory_effect_observations_table_data.bed"
        else:
            filename = f"{feature_id}_source_for_regulatory_effect_observations_table_data.tsv"

        return super().get_tsv(request, options, data, filename=filename)


class TargetEffectsView(FeatureEffectsView):
    template = "search/v1/target_reg_effects.html"
    tsv_renderer = target_data

    def get_data(self, options, feature_id) -> Pageable[RegulatoryEffectObservation]:
        if self.request.user.is_anonymous:
            reg_effects = RegEffectSearch.target_search_public(feature_id, options.get("sig_only"))
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            reg_effects = RegEffectSearch.target_search(feature_id, options.get("sig_only"))
        else:
            reg_effects = RegEffectSearch.target_search_with_private(
                feature_id, options.get("sig_only"), self.request.user.all_experiments()
            )

        return reg_effects

    def get_tsv(self, request, options, data, feature_id):
        feature = DNAFeature.objects.get(accession_id=feature_id)
        filename = f"{feature.name}_targeting_regulatory_effect_observations_table_data.tsv"
        return super().get_tsv(request, options, data, filename=filename)
