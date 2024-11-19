from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import render

from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.json_templates.v1.feature_reg_effects import feature_reg_effects
from cegs_portal.search.json_templates.v1.reg_effect import regulatory_effect
from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation
from cegs_portal.search.tsv_templates.v1.reg_effects import reg_effects as re_data
from cegs_portal.search.tsv_templates.v1.reg_effects import (
    target_reg_effects as target_data,
)
from cegs_portal.search.tsv_templates.v1.reo_features import dnafeatures as f_tsv
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, RegEffectSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    MultiResponseFormatView,
)
from cegs_portal.utils import truthy_to_bool


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


class RegEffectFeaturesView(ExperimentAccessMixin, MultiResponseFormatView):
    tsv_renderer = f_tsv

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

    def request_options(self, request):
        """
        Headers used:
            accept
                * text/tab-separated-values
        GET queries used:
            accept
                * text/tab-separated-values
        """

        options = super().request_options(request)
        options["tsv_format"] = request.GET.get("tsv_format", None)

        return options

    def get_data(self, _options, re_id):
        raise NotImplementedError("RegEffectFeaturesView.get_data")


class RegEffectSourcesView(RegEffectFeaturesView):
    def get_tsv(self, request, options, data, re_id):
        if is_bed6(options):
            filename = f"{re_id}_regulatory_effect_observations_sources.bed"
        else:
            filename = f"{re_id}_regulatory_effect_observations_sources.tsv"

        return super().get_tsv(request, options, data, filename=filename)

    def get_data(self, _options, re_id):
        return RegEffectSearch.sources_search(re_id), RegEffectSearch.id_search_basic(re_id)


class RegEffectTargetsView(RegEffectFeaturesView):
    def get_tsv(self, request, options, data, re_id):
        if is_bed6(options):
            filename = f"{re_id}_regulatory_effect_observations_targets.bed"
        else:
            filename = f"{re_id}_regulatory_effect_observations_targets.tsv"

        return super().get_tsv(request, options, data, filename=filename)

    def get_data(self, _options, re_id):
        return RegEffectSearch.targets_search(re_id), RegEffectSearch.id_search_basic(re_id)


class FeatureEffectsView(ExperimentAccessMixin, MultiResponseFormatView):
    json_renderer = feature_reg_effects
    table_partial = ""
    template = ""

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

        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        options["sig_only"] = truthy_to_bool(request.GET.get("sig_only", True))
        options["tsv_format"] = request.GET.get("tsv_format", None)

        return options

    def get(self, request, options, data, *args, **kwargs):
        regeffects, feature, dna_feature = data
        help_text = f"Regulatory effect observations targeting {dna_feature.name}"
        source_help_text = f"Regulatory effect observations in the listed genes, with { feature.get_feature_type_display() } as the source."
        reg_effect_paginator = Paginator(regeffects, options["per_page"])
        reg_effect_page = reg_effect_paginator.get_page(options["page"])
        data = {
            "regeffects": reg_effect_page,
            "feature": feature,
            "help_text": help_text,
            "source_help_text": source_help_text,
        }

        if request.headers.get("HX-Request"):
            return render(request, self.table_partial, data)

        return super().get(request, options, data, *args, **kwargs)

    def get_json(self, request, options, data, *args, **kwargs):
        regeffects, _ = data
        reg_effect_paginator = Paginator(regeffects, options["per_page"])
        reg_effect_page = reg_effect_paginator.get_page(options["page"])

        return super().get_json(request, options, reg_effect_page, *args, **kwargs)

    def get_data(self, options, feature_id) -> tuple[QuerySet[RegulatoryEffectObservation], DNAFeature, DNAFeature]:
        raise NotImplementedError("FeatureEffectsView.get_data")


class SourceEffectsView(FeatureEffectsView):
    template = "search/v1/source_reg_effects.html"
    table_partial = "search/v1/partials/_reg_effect.html"
    tsv_renderer = re_data

    def get_data(self, options, feature_id) -> tuple[QuerySet[RegulatoryEffectObservation], DNAFeature, DNAFeature]:
        feature = RegEffectSearch.id_feature_search(feature_id)
        dna_feature = DNAFeature.objects.get(accession_id=feature_id)
        if self.request.user.is_anonymous:
            reg_effects = RegEffectSearch.feature_source_search_public(feature_id, options.get("sig_only"))
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            reg_effects = RegEffectSearch.feature_source_search(feature_id, options.get("sig_only"))
        else:
            reg_effects = RegEffectSearch.feature_source_search_with_private(
                feature_id, options.get("sig_only"), self.request.user.all_experiments()
            )

        return reg_effects, feature, dna_feature

    def get_tsv(self, request, options, data, feature_id):
        if is_bed6(options):
            filename = f"{feature_id}_regulatory_effect_observations_table_data.bed"
        else:
            filename = f"{feature_id}_regulatory_effect_observations_table_data.tsv"

        return super().get_tsv(request, options, data[0], filename=filename)


class TargetEffectsView(FeatureEffectsView):
    template = "search/v1/target_reg_effects.html"
    table_partial = "search/v1/partials/_target_reg_effect.html"
    tsv_renderer = target_data

    def get_data(self, options, feature_id) -> tuple[QuerySet[RegulatoryEffectObservation], DNAFeature, DNAFeature]:
        feature = RegEffectSearch.id_feature_search(feature_id)
        dna_feature = DNAFeature.objects.get(accession_id=feature_id)
        if self.request.user.is_anonymous:
            reg_effects = RegEffectSearch.feature_target_search_public(feature_id, options.get("sig_only"))
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            reg_effects = RegEffectSearch.feature_target_search(feature_id, options.get("sig_only"))
        else:
            reg_effects = RegEffectSearch.feature_target_search_with_private(
                feature_id, options.get("sig_only"), self.request.user.all_experiments()
            )

        return reg_effects, feature, dna_feature

    def get_tsv(self, request, options, data, feature_id):
        dna_feature = DNAFeature.objects.get(accession_id=feature_id)
        if is_bed6(options):
            filename = f"{dna_feature.name}_targeting_regulatory_effect_observations_table_data.bed"
        else:
            filename = f"{dna_feature.name}_targeting_regulatory_effect_observations_table_data.tsv"

        return super().get_tsv(request, options, data[0], filename=filename)
