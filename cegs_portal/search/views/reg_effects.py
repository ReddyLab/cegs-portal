from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import RegEffectSearch
from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


def reg_effect(request, re_id):
    """
    Headers used:
        accept
            * application/json
    """
    search_results = RegEffectSearch.id_search(re_id)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_results), safe=False)

    return render(request, "search/reg_effect.html", {"regulatory_effect": search_results})
