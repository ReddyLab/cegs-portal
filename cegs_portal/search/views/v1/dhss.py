from django.core.paginator import Paginator

from cegs_portal.search.view_models.v1 import DHSSearch
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.renderers import json


class DHS(TemplateJsonView):
    template = "search/v1/dhs_exact.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            search_type
                * exact
                * like
                * start
                * in
        """
        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))
        return options

    def get(self, request, options, data, dhs_id):
        return super().get(request, options, {"dhs": data[0], "reg_effects": data[1]})

    def get_json(self, _request, options, data, dhs_id):
        json_results = {
            "dhs": json(data[0], options["json_format"]),
            "reg_effects": [json(result, options["json_format"]) for result in data[1]],
        }
        return super().get_json(_request, options, json_results)

    def get_data(self, options, dhs_id):
        dhs, reg_effects = DHSSearch.id_search(dhs_id)
        reg_effect_paginator = Paginator(reg_effects, 20)
        reg_effect_page = reg_effect_paginator.get_page(options["page"])

        for reg_effect in reg_effect_page:
            setattr(
                reg_effect,
                "co_regulators",
                [source for source in reg_effect.sources.all() if source.id != dhs.id],
            )
            co_sources = set()
            for target in reg_effect.targets.all():
                for tre in target.regulatory_effects.all():
                    co_sources.update([source for source in tre.sources.all() if source.id != dhs.id])
            setattr(reg_effect, "co_sources", co_sources)

        return dhs, reg_effect_page


class DHSLoc(TemplateJsonView):
    template = "search/v1/dhs.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            format
                * genoverse, only relevant for json
            search_type
                * exact
                * overlap
            assembly
                * free-text, but should match a genome assembly that exists in the DB
        """
        options = super().request_options(request)
        options["search_type"] = request.GET.get("search_type", "overlap")
        options["assembly"] = request.GET.get("assembly", None)
        options["region_properties"] = request.GET.getlist("property", None)
        options["response_format"] = request.GET.get("format", None)
        options["region_types"] = request.GET.getlist("region_type", ["dhs"])

        return options

    def get(self, request, options, data, chromo, start, end):
        template_data = {"dhss": data, "loc": {"chr": chromo, "start": start, "end": end}}
        return super().get(request, options, template_data)

    def get_data(self, options, chromo, start, end):
        if not chromo.startswith("chr"):
            chromo = f"chr{chromo}"

        dhs_list = DHSSearch.loc_search(
            chromo,
            start,
            end,
            options["assembly"],
            options["search_type"],
            options["region_properties"],
            region_types=options["region_types"],
        )

        return dhs_list

    def get_json(self, _request, options, data, chromo, start, end):
        return super().get_json(_request, options, [json(result, options["json_format"]) for result in data])
