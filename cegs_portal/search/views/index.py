from django.shortcuts import render

from cegs_portal.search.forms import SearchForm, SearchGeneForm, SearchLocationForm


def index(request):
    form = SearchForm()
    gene_form = SearchGeneForm()
    location_form = SearchLocationForm()
    return render(
        request,
        "search/index.html",
        {"form": form, "gene_form": gene_form, "location_form": location_form},
    )
