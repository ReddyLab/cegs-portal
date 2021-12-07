from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import DHSSearch
from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


def dhs(request, dhs_id):
    """
    Headers used:
        accept
            * application/json
    """
    search_results = DHSSearch.id_search(dhs_id)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_results), safe=False)

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

    return render(request, "search/dhs_exact.html", {"dhs": search_results})


def dhs_loc(request, chromo, start, end):
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
    search_type = request.GET.get("search_type", "overlap")
    assembly = request.GET.get("assembly", None)
    region_properties = request.GET.getlist("property", None)
    is_json = request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME
    response_format = request.GET.get("format", None)
    region_types = request.GET.getlist("region_type", ["dhs"])

    if not chromo.startswith("chr"):
        chromo = f"chr{chromo}"

    dhs_list = DHSSearch.loc_search(
        chromo, start, end, assembly, search_type, region_properties, region_types=region_types
    )

    if is_json:
        return dhs_loc_json(dhs_list, response_format)

    return render(request, "search/dhs.html", {"dhss": dhs_list, "loc": {"chr": chromo, "start": start, "end": end}})


def dhs_loc_json(dhs_list, response_format):
    results = [json(result, response_format) for result in dhs_list]

    return JsonResponse(results, safe=False)
