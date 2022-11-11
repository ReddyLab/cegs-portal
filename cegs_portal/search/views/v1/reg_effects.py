from django.core.paginator import Paginator
from django.http import Http404

from cegs_portal.search.json_templates.v1.reg_effect import (
    regulatory_effect,
    source_reg_effects,
)
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import RegEffectSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    TemplateJsonView,
)


class RegEffectView(ExperimentAccessMixin, TemplateJsonView):
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


class SourceEffectsView(TemplateJsonView):
    json_renderer = source_reg_effects
    template = "search/v1/reg_effect.html"
    template_data_name = "regulatory_effects"

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
        """
        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))

        return options

    def get_data(self, options, source_id):
        """
        Headers used:
            accept
                * application/json
        """
        reg_effects = RegEffectSearch.source_search(source_id)
        reg_effect_paginator = Paginator(reg_effects, 20)
        reg_effect_page = reg_effect_paginator.get_page(options["page"])

        for reg_effect in reg_effect_page:
            cell_lines = set()
            tissue_types = set()
            for bios in reg_effect.experiment.biosamples.all():
                cell_lines.update(bios.cell_line.name)
                tissue_types.update(bios.cell_line.tissue_type_name)
            setattr(reg_effect, "cell_lines", cell_lines)
            setattr(reg_effect, "tissue_types", tissue_types)
            # Other DHSs associated with the same Regulatory Effect
            setattr(
                reg_effect,
                "co_regulators",
                [source for source in reg_effect.sources.all() if source.id != source_id],
            )
            # Other DHSs associated with the same target as this Reg Effect
            co_sources = set()
            for target in reg_effect.targets.all():
                for tre in target.regulatory_effects.all():
                    co_sources.update([source for source in tre.sources.all() if source.id != source_id])
            setattr(reg_effect, "co_sources", co_sources)

        return reg_effect_page
