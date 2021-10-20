from urllib.parse import unquote_plus

from django.http import HttpResponseServerError
from django.shortcuts import render

from cegs_portal.search.errors import SearchResultsException
from cegs_portal.search.forms import SearchForm
from cegs_portal.search.view_models import Search


def results(request):
    search_query = unquote_plus(request.GET["query"])
    try:
        search_results = Search.search(search_query)
    except SearchResultsException as e:
        return HttpResponseServerError(e)

    search_results["form"] = SearchForm()

    return render(
        request,
        "search/results.html",
        search_results,
    )
