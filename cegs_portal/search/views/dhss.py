from django.http.response import JsonResponse

from cegs_portal.search.view_models import DHSSearch
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.renderers import json


class DHS(TemplateJsonView):
    template = "search/dhs_exact.html"
    template_data_name = "dhs"

    def get_data(self, options, dhs_id):
        search_results = DHSSearch.id_search(dhs_id)

        for reg_effect in search_results.regulatory_effects.all():
            setattr(
                reg_effect,
                "co_regulators",
                [source for source in reg_effect.sources.all() if source.id != search_results.id],
            )
            co_sources = set()
            for target in reg_effect.targets.all():
                for tre in target.regulatory_effects.all():
                    co_sources.update([source for source in tre.sources.all() if source.id != search_results.id])
            setattr(reg_effect, "co_sources", co_sources)

        return search_results


class DHSLoc(TemplateJsonView):
    template = "search/dhs.html"

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

    def get_template_prepare_data(self, data, _options, chromo, start, end):
        return {"dhss": data, "loc": {"chr": chromo, "start": start, "end": end}}

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

    def get_json(self, _request, options, data_handler, chromo, start, end):
        results = [json(result, options["json_format"]) for result in data_handler(options, chromo, start, end)]

        return JsonResponse(results, safe=False)
