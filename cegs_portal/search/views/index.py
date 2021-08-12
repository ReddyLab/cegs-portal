from django.shortcuts import render

from cegs_portal.search.forms import SearchForm


def index(request):
    form = SearchForm()
    return render(request, "search/index.html", {"form": form})
