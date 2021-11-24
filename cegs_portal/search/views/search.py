from urllib.parse import unquote_plus

from django.http import HttpResponseServerError
from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.errors import SearchResultsException
from cegs_portal.search.forms import SearchForm
from cegs_portal.search.view_models import Search
from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


def results(request):
    search_query = unquote_plus(request.GET["query"])
    is_json = request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME

    try:
        search_results = Search.search(unquote_plus(search_query))
    except SearchResultsException as e:
        return HttpResponseServerError(e)

    if is_json:
        return JsonResponse(json(search_results), safe=False)

    search_results["form"] = SearchForm()

    return render(
        request,
        "search/results.html",
        search_results,
    )
