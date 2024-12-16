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


def glossary(request):
    if request.headers.get("HX-Target") == "glossary-modal-container":
        return render(
            request,
            "search/v1/partials/_glossary.html",
        )

    return render(request, "search/v1/partials/_glossary.html")


def multi_experiments_help_page(request):
    if request.headers.get("HX-Target") == "multi-experiments-help-modal-container":
        return render(
            request,
            "search/v1/partials/_multi_experiments_help.html",
        )

    return render(request, "search/v1/partials/_multi_experiments_help.html")
