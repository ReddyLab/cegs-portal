from django.core.paginator import Paginator

from cegs_portal.search.json_templates.v1.reg_effect import (
    region_reg_effects,
    regulatory_effect,
)
from cegs_portal.search.view_models.v1 import RegEffectSearch
from cegs_portal.search.views.custom_views import TemplateJsonView


class RegEffectView(TemplateJsonView):
    json_renderer = regulatory_effect
    template = "search/v1/reg_effect.html"
    template_data_name = "regulatory_effect"

    def get_data(self, _options, re_id):
        """
        Headers used:
            accept
                * application/json
        """
        search_results = RegEffectSearch.id_search(re_id)

        cell_lines = set()
        tissue_types = set()
        for f in search_results.experiment.data_files.all():
            cell_lines.update(f.cell_lines.all())
            tissue_types.update(f.tissue_types.all())
        setattr(search_results, "cell_lines", cell_lines)
        setattr(search_results, "tissue_types", tissue_types)

        return search_results


class RegionEffectsView(TemplateJsonView):
    json_renderer = region_reg_effects
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

    def get_data(self, options, region_id):
        """
        Headers used:
            accept
                * application/json
        """
        reg_effects = RegEffectSearch.region_search(region_id)
        reg_effect_paginator = Paginator(reg_effects, 20)
        reg_effect_page = reg_effect_paginator.get_page(options["page"])

        for reg_effect in reg_effect_page:
            cell_lines = set()
            tissue_types = set()
            for lines, types in [
                (file.cell_lines.all(), file.tissue_types.all()) for file in reg_effect.experiment.data_files.all()
            ]:
                cell_lines.update(lines)
                tissue_types.update(types)
            setattr(reg_effect, "cell_lines", cell_lines)
            setattr(reg_effect, "tissue_types", tissue_types)
            # Other DHSs associated with the same Regulatory Effect
            setattr(
                reg_effect,
                "co_regulators",
                [source for source in reg_effect.sources.all() if source.id != region_id],
            )
            # Other DHSs associated with the same target as this Reg Effect
            co_sources = set()
            for target in reg_effect.target_assemblies.all():
                for tre in target.regulatory_effects.all():
                    co_sources.update([source for source in tre.sources.all() if source.id != region_id])
            setattr(reg_effect, "co_sources", co_sources)

        return reg_effect_page
