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

    cell_lines = set()
    tissue_types = set()
    for f in search_results.experiment.data_files.all():
        cell_lines.update(f.cell_lines.all())
        tissue_types.update(f.tissue_types.all())
    setattr(search_results, "cell_lines", cell_lines)
    setattr(search_results, "tissue_types", tissue_types)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_results), safe=False)

    return render(request, "search/reg_effect.html", {"regulatory_effect": search_results})
