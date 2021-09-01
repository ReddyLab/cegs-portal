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

    form = SearchForm()

    return render(
        request,
        "search/results.html",
        {
            "assemblies": search_results["assemblies"],
            "genes": search_results["genes"],
            "dh_sites": search_results["dh_sites"],
            "form": form,
        },
    )
