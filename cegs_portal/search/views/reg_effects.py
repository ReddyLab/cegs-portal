from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import DHSSearch
from cegs_portal.search.views.renderers import json

JSON_MIME = "application/json"


def dhs(request, dhs_id):
    """
    Headers used:
        accept
            * application/json
    """
    search_results = DHSSearch.id_search(dhs_id)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_results), safe=False)

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
    search_type = request.GET.get("search_type", "exact")
    assembly = request.GET.get("assembly", None)
    is_json = request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME
    response_format = request.GET.get("format", None)
    region_types = request.GET.getlist("region_type", ["dhs"])

    if not chromo.startswith("chr"):
        chromo = f"chr{chromo}"

    dhs_list = DHSSearch.loc_search(chromo, start, end, assembly, search_type, region_types=region_types)

    if is_json:
        return dhs_loc_json(dhs_list, response_format)

    return render(request, "search/dhs.html", {"dhss": dhs_list, "loc": {"chr": chromo, "start": start, "end": end}})


def dhs_loc_json(dhs_list, response_format):
    results = [json(result, response_format) for result in dhs_list]

    return JsonResponse(results, safe=False)
