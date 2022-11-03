from urllib.parse import unquote_plus

from django.core.paginator import Paginator

from cegs_portal.search.errors import SearchResultsException
from cegs_portal.search.forms import SearchForm
from cegs_portal.search.json_templates.v1.search_results import (
    search_results as sr_json,
)
from cegs_portal.search.view_models.errors import ViewModelError
from cegs_portal.search.view_models.v1 import Search
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.utils.http_exceptions import Http400, Http500


class SearchView(TemplateJsonView):
    json_renderer = sr_json
    template = "search/v1/search_results.html"

    def request_options(self, request):
        options = super().request_options(request)
        options["search_query"] = request.GET.get("query", "")
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["feature_page"] = int(request.GET.get("feature_page", 1))
        return options

    def get(self, request, options, data):
        data["form"] = SearchForm()
        return super().get(request, options, data)

    def get_data(self, options):
        unquoted_search_query = unquote_plus(options["search_query"])

        try:
            search_results = Search.search(unquoted_search_query, options["facets"])
        except SearchResultsException as e:
            raise Http500(e)
        except ViewModelError as e:
            raise Http400(e)

        search_results["query"] = options["search_query"]
        search_results["facets_query"] = options["facets"]

        if search_results["search_type"] == "LOCATION":
            feature_paginator = Paginator(search_results["features"], 20)
            search_results["features"] = feature_paginator.get_page(options["feature_page"])

        return search_results
