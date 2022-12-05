from django.core.paginator import Paginator

from cegs_portal.search.json_templates.v1.reg_effect import regulatory_effect
from cegs_portal.search.json_templates.v1.source_reg_effects import source_reg_effects
from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.search.view_models.v1 import RegEffectSearch
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.utils.pagination_types import Pageable


class RegEffectView(TemplateJsonView):
    """
    Headers used:
        accept
            * application/json
    """

    json_renderer = regulatory_effect
    template = "search/v1/reg_effect.html"
    template_data_name = "regulatory_effect"

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
    template = "search/v1/source_reg_effects.html"
    template_data_name = "regeffects"

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
        options["per_page"] = int(request.GET.get("per_page", 20))
        return options

    def get_data(self, options, source_id) -> Pageable[RegulatoryEffectObservation]:
        reg_effects = RegEffectSearch.source_search(source_id)
        reg_effect_paginator = Paginator(reg_effects, options["per_page"])
        reg_effect_page = reg_effect_paginator.get_page(options["page"])
        return reg_effect_page
