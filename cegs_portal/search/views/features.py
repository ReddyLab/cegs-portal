from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import FeatureSearch, IdType
from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


# @method_decorator(csrf_exempt, name='dispatch')
def feature(request, id_type, feature_id):
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
    search_type = request.GET.get("search_type", "exact")
    feature_types = request.GET.get("features", ["gene"])
    features = FeatureSearch.id_search(id_type, feature_id, feature_types, search_type)

    if id_type == IdType.ENSEMBL.value:
        return render(
            request,
            "search/feature_exact.html",
            {
                "feature": features.first(),
            },
        )

    results = {
        "features": features,
    }

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        return JsonResponse(
            {
                "assemblies": [json(result) for result in results["assemblies"]],
            },
            safe=False,
        )

    return render(request, "search/features.html", results)


# @method_decorator(csrf_exempt, name='dispatch') # only needed for POST, in dev.
def feature_loc(request, chromo, start, end):
    """
    Headers used:
        accept
            * application/json
    GET queries used:
        accept
            * application/json
        format
            * genoverse
        search_type
            * exact
            * overlap
        assembly
            * free-text, but should match a genome assembly that exists in the DB
    """
    search_type = request.GET.get("search_type", "overlap")
    assembly = request.GET.get("assembly", None)
    response_format = request.GET.get("format", None)
    feature_types = request.GET.getlist("feature", ["gene"])

    if chromo.isnumeric():
        chromo = f"chr{chromo}"

    assemblies = FeatureSearch.loc_search(chromo, start, end, assembly, feature_types, search_type)

    results = {
        "assemblies": list(assemblies),
    }

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        return JsonResponse([json(result, response_format) for result in results["assemblies"]], safe=False)

    return render(request, "search/features.html", results)
