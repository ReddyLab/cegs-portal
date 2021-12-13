from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import FeatureSearch, IdType
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


class FeatureEnsembl(TemplateJsonView):
    template = "search/feature_exact.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            search_type
                * exact
                * like
                * start
                * in
        """
        options = super().request_options(request)
        options["search_type"] = request.GET.get("search_type", "exact")
        options["feature_types"] = request.GET.get("features", ["gene"])
        return options

    def get_template_prepare_data(self, data, options, feature_id):
        return {"feature": data, "feature_name": "Gene"}

    def get_data(self, options, feature_id):
        features = FeatureSearch.id_search(
            IdType.ENSEMBL.value, feature_id, options["feature_types"], options["search_type"]
        )
        return features.first()


def feature(request, id_type, feature_id):
    """
    Headers used:
        accept
            * application/json
    GET queries used:
        accept
            * application/json
        search_type
            * exact
            * like
            * start
            * in
    """
    search_type = request.GET.get("search_type", "exact")
    feature_types = request.GET.get("features", ["gene"])
    features = FeatureSearch.id_search(id_type, feature_id, feature_types, search_type)

    results = {
        "features": features,
    }

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        return JsonResponse(
            {
                "assemblies": [json(result) for result in results["assemblies"]],
            },
            safe=False,
        )

    return render(request, "search/features.html", results)


class FeatureLoc(TemplateJsonView):
    template = "search/features.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            format
                * genoverse
            search_type
                * exact
                * overlap
            assembly
                * free-text, but should match a genome assembly that exists in the DB
        """
        options = super().request_options(request)
        options["search_type"] = request.GET.get("search_type", "overlap")
        options["assembly"] = request.GET.get("assembly", None)
        options["feature_types"] = request.GET.getlist("feature", ["gene"])

        return options

    def get_json(self, _request, options, data_handler, chromo, start, end):
        results = [json(result, options["json_format"]) for result in data_handler(options, chromo, start, end)]
        return JsonResponse(results, safe=False)

    def get_template_prepare_data(self, data, options, chromo, start, end):
        return {"features": data, "feature_name": "Genes"}

    def get_data(self, options, chromo, start, end):
        if chromo.isnumeric():
            chromo = f"chr{chromo}"

        assemblies = FeatureSearch.loc_search(
            chromo, start, end, options["assembly"], options["feature_types"], options["search_type"]
        )

        features = {}
        for assembly in assemblies.all():
            feature_list = features.get(assembly.feature, [])
            feature_list.append(assembly)
            features[assembly.feature] = feature_list

        return features
