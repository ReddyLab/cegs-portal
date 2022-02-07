from urllib.parse import unquote_plus

from cegs_portal.search.errors import SearchResultsException
from cegs_portal.search.forms import SearchForm
from cegs_portal.search.json_templates.v1.search_results import (
    search_results as sr_json,
)
from cegs_portal.search.view_models.v1 import Search
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.utils.http_exceptions import Http500


class SearchView(TemplateJsonView):
    json_renderer = sr_json
    template = "search/v1/search_results.html"

    def request_options(self, request):
        options = super().request_options(request)
        options["search_query"] = request.GET["query"]
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
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

        search_results["query"] = options["search_query"]
        return search_results
