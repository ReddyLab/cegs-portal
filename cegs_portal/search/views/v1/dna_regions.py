from django.core.paginator import Paginator
from django.http.response import JsonResponse

from cegs_portal.search.json_templates.v1.dna_region_exact import dnaregion
from cegs_portal.search.view_models.v1 import DNARegionSearch
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.renderers import json

DEFAULT_REGION_NAME = "DNA Region"
DEFAULT_REGION_NAME_PLURAL = "DNA Regions"
REGION_NAMES = {"dhs": "DNase I Hypersensitive Site", "ccre": "candidate Cis-Regulatory Element"}
REGION_NAMES_PLURAL = {"dhs": "DNase I Hypersensitive Sites", "ccre": "candidate Cis-Regulatory Elements"}


class DNARegion(TemplateJsonView):
    json_renderer = dnaregion
    template = "search/v1/dna_region_exact.html"

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

    def get(self, request, options, data, region_id):
        region, reg_effects = data
        rtn = REGION_NAMES.get(region.region_type, DEFAULT_REGION_NAME)
        rtns = REGION_NAMES_PLURAL.get(region.region_type, DEFAULT_REGION_NAME_PLURAL)

        template_data = {
            "region": region,
            "reg_effects": reg_effects,
            "region_type_name": rtn,
            "region_type_name_plural": rtns,
        }
        return super().get(request, options, template_data)

    def get_data(self, options, region_id):
        region, reg_effects = DNARegionSearch.id_search(region_id)
        reg_effect_paginator = Paginator(reg_effects, 20)
        reg_effect_page = reg_effect_paginator.get_page(options["page"])

        for reg_effect in reg_effect_page:
            setattr(
                reg_effect,
                "co_regulators",
                [source for source in reg_effect.sources.all() if source.id != region.id],
            )
            co_sources = set()
            for target in reg_effect.targets.all():
                for tre in target.regulatory_effects.all():
                    co_sources.update([source for source in tre.sources.all() if source.id != region.id])
            setattr(reg_effect, "co_sources", co_sources)

        return region, reg_effect_page


class DNARegionLoc(TemplateJsonView):
    template = "search/v1/dna_regions.html"

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
        options["region_properties"] = request.GET.getlist("property")
        options["response_format"] = request.GET.get("format", None)
        options["region_types"] = request.GET.getlist("region_type")

        return options

    def get(self, request, options, data, chromo, start, end):
        if len(options["region_types"]) == 1:
            rtn = REGION_NAMES_PLURAL.get(options["region_types"][0], DEFAULT_REGION_NAME_PLURAL)
        else:
            rtn = DEFAULT_REGION_NAME_PLURAL

        template_data = {
            "regions": data,
            "loc": {"chr": chromo, "start": start, "end": end},
            "region_type_name": rtn,
            "region_type_query_slug": "&".join([f"region_type={rt}" for rt in options["region_types"]]),
        }

        return super().get(request, options, template_data)

    def get_data(self, options, chromo, start, end):
        if not chromo.startswith("chr"):
            chromo = f"chr{chromo}"

        region_list = DNARegionSearch.loc_search(
            chromo,
            start,
            end,
            options["assembly"],
            options["search_type"],
            options["region_properties"],
            region_types=options["region_types"],
        )

        return region_list

    def get_json(self, _request, options, data, chromo, start, end):
        return JsonResponse([json(result, options["json_format"]) for result in data.all()], safe=False)
